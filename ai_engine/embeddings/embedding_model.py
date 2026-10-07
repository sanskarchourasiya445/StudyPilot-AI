"""
ai_engine/embeddings/embedding_model.py

Responsibility: provide a single, cached embedding model instance that
conforms to LangChain's `Embeddings` interface (embed_documents /
embed_query). This is the ONLY file that knows the embedding model's
name or how it's loaded - everything else in the engine (embedder.py,
vectorstore/chroma.py) depends only on the LangChain `Embeddings`
interface this returns.

Why local sentence-transformers instead of a paid embeddings API?
- Zero marginal cost per chunk - important for a student-facing product
  that may re-embed large PDFs/lecture transcripts frequently.
- No API key required, no network dependency for embeddings specifically
  (only the LLM call needs network + a key).
- `all-MiniLM-L6-v2` is a well-established, fast, small-footprint
  retrieval model - a reasonable default for CPU inference at this
  project's scale.

Why a singleton/cache instead of instantiating per call?
Loading a sentence-transformers model reads model weights from disk (or
downloads them once) - real, non-trivial latency. Both ingestion (many
chunks at once) and query-time (one query at a time) should reuse the
exact same loaded model instance rather than reloading it repeatedly.
"""

from __future__ import annotations

import logging
from functools import lru_cache

from langchain_huggingface import HuggingFaceEmbeddings

from ai_engine.config import EMBEDDING_DEVICE, EMBEDDING_MODEL

logger = logging.getLogger(__name__)


class EmbeddingModelError(Exception):
    """Raised when the embedding model fails to load (missing
    dependency, corrupted cache, out-of-memory, unknown model name)."""


@lru_cache(maxsize=1)
def get_embedding_model() -> HuggingFaceEmbeddings:
    """Return a cached, ready-to-use embedding model.

    `lru_cache(maxsize=1)` gives a process-wide singleton without the
    boilerplate of a manual module-level global + None-check. Since this
    function takes no arguments, there is only ever one cache entry.

    Raises:
        EmbeddingModelError: if the model fails to load.
    """
    try:
        import os
        os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
        os.environ.setdefault("OMP_NUM_THREADS", "1")
        os.environ.setdefault("MKL_NUM_THREADS", "1")
        try:
            import torch
            torch.set_num_threads(1)
            torch.set_grad_enabled(False)
        except Exception:
            pass

        logger.info(
            "Loading embedding model '%s' on device '%s' (first call may "
            "download weights)...",
            EMBEDDING_MODEL,
            EMBEDDING_DEVICE,
        )
        model = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={"device": EMBEDDING_DEVICE},
            encode_kwargs={"normalize_embeddings": True},
        )
        logger.info("Embedding model loaded successfully.")
        return model
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to load embedding model: %s", exc)
        raise EmbeddingModelError(
            f"Could not load embedding model '{EMBEDDING_MODEL}': {exc}"
        ) from exc
