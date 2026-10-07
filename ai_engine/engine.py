"""
ai_engine/engine.py

Responsibility: the ONE class a future FastAPI backend (or any other
consumer) should ever import. `AIEngine` owns the full lifecycle
(initialize once at startup) and exposes exactly one method per
capability - `ingest`, `chat`, `summarize`, `generate_notes`,
`generate_quiz`. No consumer should ever need to import
`loaders/`, `embeddings/`, `vectorstore/`, `llm/`, or `services/`
directly - that indirection is the entire point of this file, and it's
what keeps the AI Engine framework-independent: this class has zero
knowledge of FastAPI, routes, auth, or databases, and a route handler
that wraps it later is a thin translation layer, not a place where
business logic accumulates.

Why a class instead of a bag of module-level functions?
`AIEngine` holds STATE that is expensive to (re)create: the loaded
embedding model, the open vector store connection, the instantiated
Gemini client. Building these once at startup (`initialize()`) and
reusing them for every subsequent call is both a performance requirement
and a correctness one.

--------------------------------------------------------------------
v1.1 additions (all additive - no v1.0 method signature lost meaning,
no existing method removed or renamed)
--------------------------------------------------------------------
- `ingest()` gains optional `workspace_id`/`user_id` scoping and now
  generates and returns a `resource_id` per call.
- `chat()` gains optional `resource_id`/`workspace_id`/`user_id`
  filters, alongside the existing `source_filter`.
- New: `search()` - raw retrieval without an LLM call.
- New: `delete_resource()`, `list_resources()`, `get_resource()`,
  `stats()`, `workspace_stats()` - resource lifecycle/introspection.
- New: `health()`, `version()` - operational endpoints for a consuming
  backend's own health-check/status routes.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Optional

from langchain_core.documents import Document

from ai_engine.config import ENGINE_VERSION, FETCH_K, LAMBDA_MULT, TOP_K, ensure_dirs
from ai_engine.embeddings.embedding_model import get_embedding_model
from ai_engine.llm.gemini import GeminiLLM
from ai_engine.loaders.base_loader import LoaderError
from ai_engine.loaders.loader_factory import load_source
from ai_engine.preprocessing.chunker import chunk_documents
from ai_engine.preprocessing.cleaner import clean_documents
from ai_engine.preprocessing.metadata import enrich_chunk_metadata
from ai_engine.services.chat_service import ChatResult, ChatService, ChatServiceError
from ai_engine.services.notes_service import NotesService, NotesServiceError
from ai_engine.services.quiz_service import QuizQuestion, QuizService, QuizServiceError
from ai_engine.services.summary_service import SummaryService, SummaryServiceError
from ai_engine.utils.exceptions import (
    ConfigurationError,
    EngineError,
    EngineNotInitializedError,
    ResourceManagementError,
    SearchError,
)
from ai_engine.utils.helpers import new_resource_id
from ai_engine.utils.logger import configure_logging
from ai_engine.utils.summary_cache import SummaryCache
from ai_engine.vectorstore.chroma import (
    ResourceNotFoundError,
    ResourceRecord,
    ResourceStats,
    VectorStoreError,
    WorkspaceStats,
    add_documents,
    collection_size,
    delete_by_resource_id,
    get_documents_by_resource_id,
    get_documents_by_source,
    get_resource_record,
    get_vector_store,
    list_ingested_sources,
    list_resources as _list_resources,
    resource_stats as _resource_stats,
    workspace_stats as _workspace_stats,
)
from ai_engine.vectorstore.retriever import RetrieverConfigError, build_retriever

logger = logging.getLogger(__name__)


@dataclass
class IngestionResult:
    """Everything a caller needs to know about one `ingest()` call."""

    source: str
    source_type: str
    pages_or_segments: int
    chunks_created: int
    # v1.1: the resource_id assigned to every chunk from this ingestion
    # call. Added with a default so any hypothetical external code that
    # already constructs an `IngestionResult` positionally/by keyword
    # without this field continues to work unmodified.
    resource_id: str = ""


@dataclass
class EngineStatus:
    """Snapshot of engine state, useful for a future health-check /
    status endpoint."""

    initialized: bool
    ingested_sources: List[str] = field(default_factory=list)


@dataclass
class EngineHealth:
    """(v1.1) Lightweight, safe-to-call-anytime health snapshot -
    distinct from `EngineStatus` (which lists full ingested-source
    content) in that this only checks whether each underlying component
    is reachable/loaded, making it cheap enough for frequent polling by
    a backend's own `/health` endpoint."""

    initialized: bool
    vector_store_reachable: bool
    embedding_model_loaded: bool
    llm_configured: bool
    version: str = ENGINE_VERSION


class AIEngine:
    """Facade over the entire AI Engine. Construct one instance, call
    `initialize()` once, then call `ingest()` / `chat()` / `summarize()`
    / `generate_notes()` / `generate_quiz()` as many times as needed.
    """

    def __init__(self, gemini_api_key: Optional[str] = None) -> None:
        """
        Args:
            gemini_api_key: optionally override the `GEMINI_API_KEY`
            environment variable (mainly useful for tests or multi-
            tenant deployments with per-user keys).
        """
        self._gemini_api_key = gemini_api_key
        self._initialized = False

        # Populated by initialize(); typed as Optional so attribute
        # access before initialization fails predictably via the
        # `_require_initialized` guard rather than an AttributeError.
        self._vector_store = None
        self._llm: Optional[GeminiLLM] = None
        self._chat_service: Optional[ChatService] = None
        self._summary_service: Optional[SummaryService] = None
        self._notes_service: Optional[NotesService] = None
        self._quiz_service: Optional[QuizService] = None
        # v1.1: kept purely so `health()` can report whether the
        # embedding model loaded successfully, without needing to
        # re-derive that from the vector store.
        self._embedding_model = None
        self._summary_cache = SummaryCache()

    def initialize(self) -> None:
        """Load the embedding model, open the vector store, and
        instantiate the Gemini client and every service. Must be called
        once before any other method.

        Raises:
            EngineError: if any initialization step fails (embedding
            model load failure, vector store open failure, missing
            Gemini API key).
        """
        logger.info("Initializing AI Engine...")
        configure_logging()
        ensure_dirs()

        try:
            embedding_model = get_embedding_model()
            self._embedding_model = embedding_model
            self._vector_store = get_vector_store(embedding_model)
        except VectorStoreError as exc:
            raise EngineError(f"Vector store initialization failed: {exc}") from exc
        except Exception as exc:  # noqa: BLE001 - embedding model load failure
            raise EngineError(f"Embedding model initialization failed: {exc}") from exc

        try:
            self._llm = GeminiLLM(api_key=self._gemini_api_key)
        except Exception as exc:  # noqa: BLE001
            raise ConfigurationError(f"LLM initialization failed: {exc}") from exc

        self._summary_service = SummaryService(self._llm)
        self._notes_service = NotesService(self._llm)
        self._quiz_service = QuizService(self._llm)

        self._initialized = True
        logger.info("AI Engine initialized successfully.")

    def _require_initialized(self) -> None:
        if not self._initialized:
            raise EngineNotInitializedError(
                "AIEngine.initialize() must be called before using this method."
            )

    def status(self) -> EngineStatus:
        """Return a snapshot of the engine's current state."""
        if not self._initialized:
            return EngineStatus(initialized=False)
        return EngineStatus(
            initialized=True,
            ingested_sources=list_ingested_sources(self._vector_store),
        )

    def ingest(
        self,
        source: str,
        workspace_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> IngestionResult:
        """Load, clean, chunk, and store one source (a PDF path, a TXT
        path, or a YouTube URL) into the workspace's vector store.

        This is incremental: calling `ingest()` multiple times (once per
        upload) grows the same workspace rather than rebuilding it - see
        `vectorstore.chroma`'s module docstring for why.

        Args:
            source: a file path (PDF/TXT) or URL (YouTube).
            workspace_id: (v1.1, optional) tags every resulting chunk
                with this workspace scope, so `chat`/`search` can later
                be restricted to it. Existing callers that omit this
                keep working exactly as before (chunks get
                `workspace_id=None`).
            user_id: (v1.1, optional) same as `workspace_id`, but for
                per-user scoping.

        Returns:
            An `IngestionResult` including the newly generated
            `resource_id` for this ingestion - the identifier to pass to
            `delete_resource`, `get_resource`, `stats`, `summarize`-by-
            resource, etc.

        Raises:
            EngineError: if loading, cleaning, chunking, or storing the
            source fails at any stage.
        """
        self._require_initialized()

        try:
            raw_documents = load_source(source)
        except LoaderError as exc:
            raise EngineError(f"Failed to load source '{source}': {exc}") from exc

        source_type = raw_documents[0].metadata.get("source_type", "unknown")
        resource_id = new_resource_id()

        cleaned = clean_documents(raw_documents)
        chunks = chunk_documents(cleaned)
        enriched = enrich_chunk_metadata(
            chunks,
            resource_id=resource_id,
            workspace_id=workspace_id,
            user_id=user_id,
            resource_type=source_type,
        )

        try:
            add_documents(self._vector_store, enriched)
        except VectorStoreError as exc:
            raise EngineError(f"Failed to store chunks for '{source}': {exc}") from exc

        logger.info(
            "Ingested '%s' (%s, resource_id=%s): %d page(s)/segment(s) -> %d chunk(s).",
            source,
            source_type,
            resource_id,
            len(raw_documents),
            len(enriched),
        )
        return IngestionResult(
            source=source,
            source_type=source_type,
            pages_or_segments=len(raw_documents),
            chunks_created=len(enriched),
            resource_id=resource_id,
        )

    def chat(
        self,
        question: str,
        source_filter: Optional[str] = None,
        resource_id: Optional[str] = None,
        resource_ids: Optional[List[str]] = None,
        workspace_id: Optional[str] = None,
        user_id: Optional[str] = None,
        history: Optional[List[dict]] = None,
    ) -> ChatResult:
        """Answer a question, optionally scoped to one ingested source.

        Args:
            question: the student's question.
            source_filter: if given, restrict retrieval to chunks from
            this one ingested `source` (see `vectorstore.retriever`).
            resource_id: (v1.1) if given, restrict retrieval to one
            specific ingested resource.
            resource_ids: (v1.1) if given, restrict retrieval to multiple
            specific ingested resources.
            workspace_id: (v1.1) if given, restrict retrieval to one
            workspace.
            user_id: (v1.1) if given, restrict retrieval to one user's
            resources.
            history: (v1.1) optional recent conversation history turns.
            Any combination of the above may be given together; existing
            callers passing only `source_filter` (or nothing) behave
            exactly as in v1.0.

        Raises:
            EngineError: if retrieval or generation fails.
        """
        self._require_initialized()
        retriever = build_retriever(
            self._vector_store,
            source_filter=source_filter,
            resource_id=resource_id,
            resource_ids=resource_ids,
            workspace_id=workspace_id,
            user_id=user_id,
        )
        chat_service = ChatService(retriever=retriever, llm=self._llm)

        try:
            return chat_service.ask(question, history=history)
        except ChatServiceError as exc:
            raise EngineError(f"Chat failed: {exc}") from exc

    # Backward compatibility alias
    ask = chat

    def search(
        self,
        query: str,
        top_k: int = TOP_K,
        fetch_k: int = FETCH_K,
        lambda_mult: float = LAMBDA_MULT,
        source_filter: Optional[str] = None,
        resource_id: Optional[str] = None,
        resource_ids: Optional[List[str]] = None,
        workspace_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> List[Document]:
        """(v1.1) Raw retrieval - return the chunks that best match
        `query`, WITHOUT calling the LLM.

        This is what a consuming backend uses for anything that wants
        "what's relevant to X" without needing a generated answer (e.g.
        a search-results UI, or a debugging/inspection endpoint) - unlike
        `chat()`, this never touches Gemini and therefore never incurs
        an LLM call.

        Args:
            query: free-text search query.
            top_k / fetch_k / lambda_mult: MMR retrieval tuning (see
            `vectorstore.retriever.build_retriever`).
            source_filter / resource_id / resource_ids / workspace_id / user_id: same
            optional scoping as `chat()`.

        Raises:
            SearchError: if retrieval fails, or if the retriever
            configuration itself is invalid (e.g. fetch_k < top_k).
        """
        self._require_initialized()

        try:
            retriever = build_retriever(
                self._vector_store,
                top_k=top_k,
                fetch_k=fetch_k,
                lambda_mult=lambda_mult,
                source_filter=source_filter,
                resource_id=resource_id,
                resource_ids=resource_ids,
                workspace_id=workspace_id,
                user_id=user_id,
            )
        except RetrieverConfigError as exc:
            raise SearchError(f"Invalid search configuration: {exc}") from exc

        try:
            return retriever.invoke(query)
        except Exception as exc:  # noqa: BLE001
            raise SearchError(f"Search failed for query {query!r}: {exc}") from exc

    def _get_source_documents(self, source: str, resource_id: Optional[str] = None) -> List:
        """Fetch every chunk for one ingested source or resource_id, or raise
        EngineError if none are found - shared by summarize/notes/quiz below."""
        try:
            documents = []
            if resource_id:
                documents = get_documents_by_resource_id(self._vector_store, resource_id)
            if not documents:
                documents = get_documents_by_resource_id(self._vector_store, source)
            if not documents:
                documents = get_documents_by_source(self._vector_store, source)
        except VectorStoreError as exc:
            raise EngineError(f"Failed to fetch chunks for '{resource_id or source}': {exc}") from exc

        if not documents:
            target = resource_id or source
            raise EngineError(
                f"No ingested content found for '{target}'. "
                f"Has it been ingested yet?"
            )
        return documents

    def summarize(
        self,
        source: str,
        resource_id: Optional[str] = None,
        force_regenerate: bool = False,
    ) -> str:
        """Summarize one previously-ingested source in full.

        Args:
            source: human-readable source name or resource_id.
            resource_id: (v1.1, optional) restrict strictly to this resource_id.
            force_regenerate: (optional) if True, bypasses the summary cache and
            forces a fresh LLM summarization.

        Raises:
            EngineError: if the source has no ingested chunks, or
            summarization fails.
        """
        self._require_initialized()
        documents = self._get_source_documents(source, resource_id=resource_id)
        
        target_res_id = resource_id or documents[0].metadata.get("resource_id") or source

        if target_res_id and not force_regenerate:
            cached_record = self._summary_cache.get(target_res_id)
            if cached_record:
                logger.info("Returning cached summary for '%s' (0 LLM calls).", target_res_id)
                return cached_record.summary

        try:
            summary = self._summary_service.summarize(documents)
            if target_res_id:
                self._summary_cache.set(target_res_id, source, summary)
            return summary
        except SummaryServiceError as exc:
            raise EngineError(f"Summarization failed for '{source}': {exc}") from exc

    def generate_notes(
        self,
        source: str,
        style: str = "bullet",
        resource_id: Optional[str] = None,
        force_regenerate: bool = False,
    ) -> str:
        """Generate study notes for one previously-ingested source.

        Args:
            source: human-readable source name or resource_id.
            style: "bullet" or "cornell".
            resource_id: (v1.1, optional) restrict strictly to this resource_id.
            force_regenerate: (optional) if True, forces re-summarization before generating notes.

        Raises:
            EngineError: if the source has no ingested chunks, `style`
            is invalid, or generation fails.
        """
        self._require_initialized()
        documents = self._get_source_documents(source, resource_id=resource_id)
        summary = self.summarize(source, resource_id=resource_id, force_regenerate=force_regenerate)
        try:
            return self._notes_service.generate_notes(documents, style=style, summary_text=summary)
        except NotesServiceError as exc:
            raise EngineError(f"Notes generation failed for '{source}': {exc}") from exc

    def generate_quiz(
        self,
        source: str,
        question_count: int = 5,
        difficulty: str = "medium",
        resource_id: Optional[str] = None,
        force_regenerate: bool = False,
    ) -> List[QuizQuestion]:
        """Generate a multiple-choice quiz for one previously-ingested
        source.

        Args:
            source: human-readable source name or resource_id.
            question_count: number of questions to generate.
            difficulty: "easy", "medium", or "hard".
            resource_id: (v1.1, optional) restrict strictly to this resource_id.
            force_regenerate: (optional) if True, forces re-summarization before generating quiz.

        Raises:
            EngineError: if the source has no ingested chunks,
            parameters are invalid, generation fails, or the LLM's
            response could not be parsed.
        """
        self._require_initialized()
        documents = self._get_source_documents(source, resource_id=resource_id)
        summary = self.summarize(source, resource_id=resource_id, force_regenerate=force_regenerate)
        try:
            return self._quiz_service.generate_quiz(
                documents,
                question_count=question_count,
                difficulty=difficulty,
                summary_text=summary,
            )
        except QuizServiceError as exc:
            raise EngineError(f"Quiz generation failed for '{source}': {exc}") from exc

    # ===================================================================
    # v1.1 additions below. Nothing above this line changes v1.0 behavior
    # for any existing caller that doesn't pass the new optional
    # arguments introduced above.
    # ===================================================================

    def delete_resource(self, resource_id: str) -> int:
        """Delete every chunk belonging to one ingested resource.

        This is the operation a consuming backend calls when a user
        deletes a Resource row - without it, deleted resources would
        remain permanently retrievable/summarizable in the vector store.

        Args:
            resource_id: the resource to remove (as returned by
            `ingest()`'s `IngestionResult.resource_id`).

        Returns:
            The number of chunks deleted.

        Raises:
            ResourceManagementError: if `resource_id` does not exist, or
            the delete operation fails.
        """
        self._require_initialized()
        self._summary_cache.invalidate(resource_id)
        try:
            return delete_by_resource_id(self._vector_store, resource_id)
        except ResourceNotFoundError as exc:
            raise ResourceManagementError(
                f"Cannot delete resource '{resource_id}': {exc}"
            ) from exc
        except VectorStoreError as exc:
            raise ResourceManagementError(
                f"Failed to delete resource '{resource_id}': {exc}"
            ) from exc

    def list_resources(self) -> List[ResourceRecord]:
        """Return a `ResourceRecord` for every ingested resource
        currently in the vector store (across all workspaces/users - a
        consuming backend is expected to further filter by its own
        authorization rules if needed).

        Raises:
            ResourceManagementError: if the underlying fetch fails.
        """
        self._require_initialized()
        try:
            return _list_resources(self._vector_store)
        except VectorStoreError as exc:
            raise ResourceManagementError(f"Failed to list resources: {exc}") from exc

    def get_resource(self, resource_id: str) -> ResourceRecord:
        """Return the `ResourceRecord` for one specific resource.

        Raises:
            ResourceManagementError: if `resource_id` does not exist, or
            the underlying fetch fails.
        """
        self._require_initialized()
        try:
            return get_resource_record(self._vector_store, resource_id)
        except ResourceNotFoundError as exc:
            raise ResourceManagementError(f"Resource '{resource_id}' not found: {exc}") from exc
        except VectorStoreError as exc:
            raise ResourceManagementError(
                f"Failed to fetch resource '{resource_id}': {exc}"
            ) from exc

    def stats(self, resource_id: str) -> ResourceStats:
        """Return content statistics (chunk count, character totals) for
        one resource.

        Raises:
            ResourceManagementError: if `resource_id` does not exist, or
            the underlying fetch fails.
        """
        self._require_initialized()
        try:
            return _resource_stats(self._vector_store, resource_id)
        except ResourceNotFoundError as exc:
            raise ResourceManagementError(f"Resource '{resource_id}' not found: {exc}") from exc
        except VectorStoreError as exc:
            raise ResourceManagementError(
                f"Failed to compute stats for '{resource_id}': {exc}"
            ) from exc

    def workspace_stats(self, workspace_id: Optional[str] = None) -> WorkspaceStats:
        """Return aggregate resource/chunk statistics, optionally scoped
        to one workspace. If `workspace_id` is omitted, aggregates
        across the entire vector store.

        Raises:
            ResourceManagementError: if the underlying fetch fails.
        """
        self._require_initialized()
        try:
            return _workspace_stats(self._vector_store, workspace_id)
        except VectorStoreError as exc:
            raise ResourceManagementError(f"Failed to compute workspace stats: {exc}") from exc

    def health(self) -> EngineHealth:
        """Lightweight, safe-to-call-anytime health check.

        Deliberately does NOT raise `EngineNotInitializedError` (unlike
        every other method on this class) - a health check that itself
        requires the engine to be healthy to call is not useful to a
        backend's own health-check endpoint, which may poll this before
        or during startup.
        """
        if not self._initialized:
            return EngineHealth(
                initialized=False,
                vector_store_reachable=False,
                embedding_model_loaded=False,
                llm_configured=False,
            )

        vector_store_reachable = True
        try:
            collection_size(self._vector_store)
        except Exception:  # noqa: BLE001 - health checks must never raise
            vector_store_reachable = False

        return EngineHealth(
            initialized=True,
            vector_store_reachable=vector_store_reachable,
            embedding_model_loaded=self._embedding_model is not None,
            llm_configured=self._llm is not None,
        )

    def version(self) -> str:
        """Return the AI Engine's version string."""
        return ENGINE_VERSION