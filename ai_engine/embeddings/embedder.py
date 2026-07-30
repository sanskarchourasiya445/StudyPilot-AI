"""
ai_engine/embeddings/embedder.py

Responsibility: a thin domain wrapper around the raw embedding model
that exposes exactly the operations the rest of the engine needs
(embed a batch of chunks, embed a single query), independent of which
underlying LangChain `Embeddings` implementation is in use.

Why does this need to exist separately from `embedding_model.py`?
`embedding_model.py` answers "how do I get a loaded, cached embedding
model instance?" - a concern about MODEL LIFECYCLE. `Embedder` answers
"how does the engine actually use that model?" - a concern about USAGE.
Today Chroma (`vectorstore/chroma.py`) embeds documents internally via
`Chroma.from_documents(embedding=...)` and never calls `Embedder`
directly, but this class exists so that:
  1. Any code that needs raw vectors directly (debugging, similarity
     scoring outside the vector store, a future non-Chroma backend)
     has one obvious place to get them, instead of reaching into
     `embedding_model.py` and calling LangChain's raw interface itself.
  2. Swapping the underlying embedding provider only ever requires
     changing `embedding_model.py` - `Embedder`'s public surface
     (`embed_documents` / `embed_query`) never has to change.
"""

from __future__ import annotations

import logging
from typing import List

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from ai_engine.embeddings.embedding_model import get_embedding_model

logger = logging.getLogger(__name__)


class Embedder:
    """Domain-facing wrapper around a LangChain `Embeddings` instance.

    Constructed with an explicit `Embeddings` dependency (defaulting to
    the cached singleton from `embedding_model.py`) rather than reaching
    for the singleton internally on every call - this is what lets a
    test construct an `Embedder` with a fake/mock `Embeddings`
    implementation without needing to load a real model.
    """

    def __init__(self, embeddings: Embeddings | None = None) -> None:
        self._embeddings: Embeddings = embeddings or get_embedding_model()

    @property
    def embeddings(self) -> Embeddings:
        """Expose the underlying LangChain `Embeddings` instance, since
        `vectorstore/chroma.py` needs to pass it directly to
        `Chroma.from_documents(embedding=...)`."""
        return self._embeddings

    def embed_documents(self, documents: List[Document]) -> List[List[float]]:
        """Embed a batch of chunks and return their raw vectors.

        Not used by the default Chroma-backed pipeline (Chroma embeds
        internally), but available for callers that need vectors
        directly rather than going through a vector store.
        """
        if not documents:
            logger.warning("embed_documents called with an empty document list.")
            return []

        texts = [doc.page_content for doc in documents]
        vectors = self._embeddings.embed_documents(texts)
        logger.debug("Embedded %d document(s).", len(documents))
        return vectors

    def embed_query(self, query: str) -> List[float]:
        """Embed a single query string and return its raw vector."""
        if not query or not query.strip():
            raise ValueError("Cannot embed an empty query string.")
        return self._embeddings.embed_query(query)
