"""
ai_engine/vectorstore/chroma.py

Responsibility: the ONLY file in the engine that imports/knows about
ChromaDB directly. Every other module talks to "the vector store"
through the functions defined here. Swapping Chroma for another vector
database (Qdrant, Weaviate, pgvector...) means rewriting this file only.

Key design difference from a typical "one-shot ingest at startup" RAG
demo: StudyPilot is a workspace a student adds documents/videos to
OVER TIME (upload a PDF today, another lecture tomorrow), not a single
corpus embedded once and then only queried. So this module is built
around INCREMENTAL ingestion (`add_documents`, called once per
`AIEngine.ingest()` call) rather than a single "build the whole
collection now" function - the vector store is opened once at engine
startup and then grows across the app's lifetime.

--------------------------------------------------------------------
v1.1 addition: resource-level lifecycle operations
--------------------------------------------------------------------
Alongside the original add/fetch-by-source functions, this file now
also owns everything keyed by `resource_id` (see
`preprocessing/metadata.py`): deleting a resource's chunks
(`delete_by_resource_id`), listing every ingested resource
(`list_resources`), fetching one resource's record or full content
(`get_resource_record`, `get_documents_by_resource_id`), and computing
per-resource/per-workspace statistics (`resource_stats`,
`workspace_stats`). These are additive - every v1.0 function below is
untouched and still behaves exactly as before.
"""

from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from ai_engine.config import CHROMA_COLLECTION_NAME, VECTOR_DB_DIR

logger = logging.getLogger(__name__)


class VectorStoreError(Exception):
    """Raised for any failure opening, creating, reading from, or
    writing to the vector store."""


class ResourceNotFoundError(VectorStoreError):
    """Raised (v1.1) when a resource-level operation (delete, fetch,
    stats) references a `resource_id` that has no chunks in the vector
    store - either it was never ingested, or it was already deleted."""


def get_vector_store(embeddings: Embeddings) -> Chroma:
    """Open (or lazily create, if none exists yet on disk) the
    persisted Chroma collection.

    Safe to call whether or not a collection already exists at
    VECTOR_DB_DIR - Chroma creates an empty one on first use if needed,
    which is exactly the behavior `AIEngine.initialize()` wants: it
    should never fail just because this is the very first document ever
    ingested into a fresh workspace.

    Raises:
        VectorStoreError: if the store cannot be opened (e.g. permission
        error on the persist directory, corrupted collection metadata).
    """
    try:
        VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)
        store = Chroma(
            collection_name=CHROMA_COLLECTION_NAME,
            embedding_function=embeddings,
            persist_directory=str(VECTOR_DB_DIR),
        )
        logger.info("Opened Chroma collection '%s' at %s", CHROMA_COLLECTION_NAME, VECTOR_DB_DIR)
        return store
    except Exception as exc:  # noqa: BLE001
        raise VectorStoreError(f"Failed to open vector store: {exc}") from exc


DEFAULT_CHROMA_BATCH_SIZE = 16


def add_documents(
    vector_store: Chroma,
    documents: List[Document],
    batch_size: int = DEFAULT_CHROMA_BATCH_SIZE,
) -> List[str]:
    """Add new chunks to an already-open vector store in bounded batches, persisting them.

    Batching prevents high memory spikes in memory-constrained environments (e.g. Render Free 512MB).

    This is the incremental-ingestion entry point `AIEngine.ingest()`
    calls after loading/cleaning/chunking a new source - it never
    rebuilds the whole collection, it only ever appends to it.

    Returns:
        The list of Chroma-assigned document IDs for the newly added
        chunks (useful if a caller later wants to support deletion of a
        specific ingested source).

    Raises:
        VectorStoreError: if adding documents fails, or if called with
        an empty list (a caller bug - ingest() should never reach this
        with zero chunks).
    """
    if not documents:
        raise VectorStoreError("Cannot add zero documents to the vector store.")

    total_docs = len(documents)
    all_ids: List[str] = []
    effective_batch_size = max(1, batch_size)

    try:
        for i in range(0, total_docs, effective_batch_size):
            batch = documents[i : i + effective_batch_size]
            batch_ids = vector_store.add_documents(batch)
            all_ids.extend(batch_ids)
            logger.debug(
                "Added batch %d-%d of %d chunks to vector store.",
                i + 1,
                min(i + effective_batch_size, total_docs),
                total_docs,
            )
        logger.info("Added %d chunk(s) in total to the vector store.", total_docs)
        import gc
        gc.collect()
        return all_ids
    except Exception as exc:  # noqa: BLE001
        raise VectorStoreError(f"Failed to add documents to vector store: {exc}") from exc


def collection_size(vector_store: Chroma) -> int:
    """Return the number of vectors currently stored.

    Used by `AIEngine` to report ingestion progress and by
    `services/chat_service.py`-adjacent code to short-circuit queries
    against a completely empty workspace before even building a
    retriever.
    """
    try:
        # LangChain's Chroma wrapper does not expose a public count() as
        # of this writing; this is a deliberate, documented use of the
        # underlying client rather than reimplementing collection
        # introspection ourselves.
        return vector_store._collection.count()  # noqa: SLF001
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not read vector store collection size: %s", exc)
        return 0


def get_documents_by_source(vector_store: Chroma, source: str) -> List[Document]:
    """Fetch every chunk belonging to one ingested source (by its
    `source` metadata value - a PDF filename, TXT filename, or YouTube
    video title), in `chunk_index` order.

    This is what makes per-source summary/notes/quiz generation
    possible: those services need the FULL content of one document, not
    just the top-k chunks a similarity/MMR retriever would return for a
    query - there is no "question" to retrieve against when the goal is
    "summarize this whole PDF".

    Raises:
        VectorStoreError: if the underlying fetch fails.
    """
    try:
        result = vector_store.get(where={"source": source}, include=["documents", "metadatas"])
    except Exception as exc:  # noqa: BLE001
        raise VectorStoreError(f"Failed to fetch chunks for source '{source}': {exc}") from exc

    documents = [
        Document(page_content=text, metadata=meta)
        for text, meta in zip(result.get("documents", []), result.get("metadatas", []))
    ]

    if not documents:
        logger.warning("No chunks found in vector store for source '%s'.", source)
        return []

    documents.sort(key=lambda doc: doc.metadata.get("chunk_index", 0))
    logger.info("Fetched %d chunk(s) for source '%s'.", len(documents), source)
    return documents


def list_ingested_sources(vector_store: Chroma) -> List[str]:
    """Return the distinct set of `source` values currently stored.

    Useful for a future UI/API layer to show "what's in my workspace"
    without needing its own separate bookkeeping of ingested sources -
    the vector store's metadata is the single source of truth.
    """
    try:
        result = vector_store.get(include=["metadatas"])
    except Exception as exc:  # noqa: BLE001
        raise VectorStoreError(f"Failed to list ingested sources: {exc}") from exc

    sources = {meta.get("source", "unknown") for meta in result.get("metadatas", [])}
    return sorted(sources)


# =======================================================================
# v1.1 additions below. Nothing above this line was modified.
# =======================================================================


def build_metadata_filter(
    source: Optional[str] = None,
    resource_id: Optional[str] = None,
    resource_ids: Optional[List[str]] = None,
    workspace_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> Optional[dict]:
    """Compose a Chroma `where` filter from any combination of the given
    metadata scopes, or return None if none were given (meaning "no
    filter - search the whole workspace").

    A single scope produces a flat `{"key": value}` filter, identical to
    what v1.0's `source_filter`-only code produced (so existing callers
    passing just `source` see byte-identical filter behavior). Two or
    more scopes are combined with Chroma's `$and` operator.

    Used by both `vectorstore/retriever.py` (to scope MMR retrieval) and
    indirectly by `AIEngine` for `search()`/`chat()` filtering.
    """
    clauses = []
    if source:
        clauses.append({"source": source})
    if resource_ids:
        if len(resource_ids) == 1:
            clauses.append({"resource_id": resource_ids[0]})
        elif len(resource_ids) > 1:
            clauses.append({"resource_id": {"$in": resource_ids}})
    elif resource_id:
        clauses.append({"resource_id": resource_id})
    if workspace_id:
        clauses.append({"workspace_id": workspace_id})
    if user_id:
        clauses.append({"user_id": user_id})

    if not clauses:
        return None
    if len(clauses) == 1:
        return clauses[0]
    return {"$and": clauses}


def get_documents_by_resource_id(vector_store: Chroma, resource_id: str) -> List[Document]:
    """Fetch every chunk belonging to one ingested resource by its
    `resource_id`, in `chunk_index` order.

    This is the resource_id-keyed counterpart to `get_documents_by_source`
    - preferred going forward since `resource_id` (unlike `source`, a
    human-readable filename/title) is guaranteed unique per ingestion,
    so it cannot collide across two different resources that happen to
    share a name.

    Raises:
        VectorStoreError: if the underlying fetch fails.
    """
    try:
        result = vector_store.get(
            where={"resource_id": resource_id}, include=["documents", "metadatas"]
        )
    except Exception as exc:  # noqa: BLE001
        raise VectorStoreError(
            f"Failed to fetch chunks for resource_id '{resource_id}': {exc}"
        ) from exc

    documents = [
        Document(page_content=text, metadata=meta)
        for text, meta in zip(result.get("documents", []), result.get("metadatas", []))
    ]

    if not documents:
        logger.warning("No chunks found in vector store for resource_id '%s'.", resource_id)
        return []

    documents.sort(key=lambda doc: doc.metadata.get("chunk_index", 0))
    logger.info("Fetched %d chunk(s) for resource_id '%s'.", len(documents), resource_id)
    return documents


def delete_by_resource_id(vector_store: Chroma, resource_id: str) -> int:
    """Delete every chunk belonging to one resource from the vector
    store.

    Args:
        vector_store: an already-open Chroma store.
        resource_id: the resource to remove.

    Returns:
        The number of chunks deleted.

    Raises:
        ResourceNotFoundError: if no chunks exist for `resource_id`
        (nothing to delete - almost certainly a caller bug, e.g. an
        already-deleted or never-ingested resource, so this is
        surfaced rather than silently treated as a no-op success).
        VectorStoreError: if the delete operation itself fails.
    """
    try:
        existing = vector_store.get(where={"resource_id": resource_id}, include=[])
    except Exception as exc:  # noqa: BLE001
        raise VectorStoreError(
            f"Failed to check existence of resource_id '{resource_id}' before deletion: {exc}"
        ) from exc

    chunk_ids = existing.get("ids", [])
    if not chunk_ids:
        raise ResourceNotFoundError(
            f"No chunks found for resource_id '{resource_id}' - nothing to delete."
        )

    try:
        vector_store.delete(where={"resource_id": resource_id})
    except Exception as exc:  # noqa: BLE001
        raise VectorStoreError(
            f"Failed to delete chunks for resource_id '{resource_id}': {exc}"
        ) from exc

    logger.info("Deleted %d chunk(s) for resource_id '%s'.", len(chunk_ids), resource_id)
    return len(chunk_ids)


@dataclass
class ResourceRecord:
    """Summary record for one ingested resource - the return type of
    `list_resources` and `get_resource_record`."""

    resource_id: str
    source: str
    resource_type: str
    workspace_id: Optional[str]
    user_id: Optional[str]
    uploaded_at: Optional[str]
    chunk_count: int


def list_resources(vector_store: Chroma) -> List[ResourceRecord]:
    """Return one `ResourceRecord` per distinct `resource_id` currently
    stored, each summarizing that resource's identity and chunk count.

    This is the resource-aware counterpart to `list_ingested_sources` -
    kept as a separate function (rather than replacing it) since
    `list_ingested_sources` returns plain source-name strings, which
    existing callers may already depend on; `list_resources` returns
    richer, resource_id-keyed records for v1.1 consumers (e.g. a
    backend's "GET /resources" endpoint).

    Raises:
        VectorStoreError: if the underlying fetch fails.
    """
    try:
        result = vector_store.get(include=["metadatas"])
    except Exception as exc:  # noqa: BLE001
        raise VectorStoreError(f"Failed to list resources: {exc}") from exc

    by_resource: Dict[str, List[dict]] = {}
    for meta in result.get("metadatas", []):
        resource_id = meta.get("resource_id")
        if not resource_id:
            # Chunks ingested before v1.1 (no resource_id in their
            # metadata) are skipped here rather than crashing - they
            # remain fully queryable via `list_ingested_sources` /
            # `get_documents_by_source` as before.
            continue
        by_resource.setdefault(resource_id, []).append(meta)

    records = [
        ResourceRecord(
            resource_id=resource_id,
            source=metas[0].get("source", "unknown"),
            resource_type=metas[0].get("resource_type", metas[0].get("source_type", "unknown")),
            workspace_id=metas[0].get("workspace_id"),
            user_id=metas[0].get("user_id"),
            uploaded_at=metas[0].get("uploaded_at"),
            chunk_count=len(metas),
        )
        for resource_id, metas in by_resource.items()
    ]

    logger.info("Listed %d ingested resource(s).", len(records))
    return records


def get_resource_record(vector_store: Chroma, resource_id: str) -> ResourceRecord:
    """Return the `ResourceRecord` for one specific resource.

    Raises:
        ResourceNotFoundError: if no chunks exist for `resource_id`.
        VectorStoreError: if the underlying fetch fails.
    """
    try:
        result = vector_store.get(where={"resource_id": resource_id}, include=["metadatas"])
    except Exception as exc:  # noqa: BLE001
        raise VectorStoreError(
            f"Failed to fetch resource record for '{resource_id}': {exc}"
        ) from exc

    metadatas = result.get("metadatas", [])
    if not metadatas:
        raise ResourceNotFoundError(f"No resource found with resource_id '{resource_id}'.")

    return ResourceRecord(
        resource_id=resource_id,
        source=metadatas[0].get("source", "unknown"),
        resource_type=metadatas[0].get("resource_type", metadatas[0].get("source_type", "unknown")),
        workspace_id=metadatas[0].get("workspace_id"),
        user_id=metadatas[0].get("user_id"),
        uploaded_at=metadatas[0].get("uploaded_at"),
        chunk_count=len(metadatas),
    )


@dataclass
class ResourceStats:
    """Detailed statistics for one resource - the return type of
    `resource_stats`. A superset of `ResourceRecord`'s identity fields,
    plus content-derived numbers that require fetching full chunk text
    (not just metadata), which is why this is a separate, slightly more
    expensive function rather than folded into `get_resource_record`."""

    resource_id: str
    source: str
    resource_type: str
    chunk_count: int
    total_characters: int
    average_chunk_characters: float


def resource_stats(vector_store: Chroma, resource_id: str) -> ResourceStats:
    """Compute content statistics for one resource.

    Raises:
        ResourceNotFoundError: if no chunks exist for `resource_id`.
        VectorStoreError: if the underlying fetch fails.
    """
    documents = get_documents_by_resource_id(vector_store, resource_id)
    if not documents:
        raise ResourceNotFoundError(f"No resource found with resource_id '{resource_id}'.")

    total_characters = sum(len(doc.page_content) for doc in documents)
    chunk_count = len(documents)
    first_meta = documents[0].metadata

    return ResourceStats(
        resource_id=resource_id,
        source=first_meta.get("source", "unknown"),
        resource_type=first_meta.get("resource_type", first_meta.get("source_type", "unknown")),
        chunk_count=chunk_count,
        total_characters=total_characters,
        average_chunk_characters=round(total_characters / chunk_count, 2),
    )


@dataclass
class WorkspaceStats:
    """Aggregate statistics across every resource in one workspace (or
    across the entire vector store, if no `workspace_id` is given)."""

    workspace_id: Optional[str]
    total_resources: int
    total_chunks: int
    resource_type_breakdown: Dict[str, int] = field(default_factory=dict)


def workspace_stats(vector_store: Chroma, workspace_id: Optional[str] = None) -> WorkspaceStats:
    """Aggregate resource/chunk counts, optionally scoped to one
    workspace.

    Args:
        vector_store: an already-open Chroma store.
        workspace_id: if given, only resources tagged with this
            workspace_id are counted. If None, aggregates across the
            entire vector store (every workspace).

    Raises:
        VectorStoreError: if the underlying fetch fails.
    """
    try:
        if workspace_id:
            result = vector_store.get(
                where={"workspace_id": workspace_id}, include=["metadatas"]
            )
        else:
            result = vector_store.get(include=["metadatas"])
    except Exception as exc:  # noqa: BLE001
        raise VectorStoreError(f"Failed to compute workspace stats: {exc}") from exc

    metadatas = result.get("metadatas", [])
    resource_ids = {meta.get("resource_id") for meta in metadatas if meta.get("resource_id")}
    type_breakdown = Counter(
        meta.get("resource_type", meta.get("source_type", "unknown")) for meta in metadatas
    )

    return WorkspaceStats(
        workspace_id=workspace_id,
        total_resources=len(resource_ids),
        total_chunks=len(metadatas),
        resource_type_breakdown=dict(type_breakdown),
    )