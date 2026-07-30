"""
ai_engine/utils/exceptions.py

Responsibility: the small set of exceptions that are genuinely
cross-cutting - not owned by any single layer (loaders, embeddings,
vector store, LLM, services). Each of those layers already defines its
own focused exception at the top of its own file (e.g. `LoaderError` in
`loaders/base_loader.py`, `EmbeddingModelError` in
`embeddings/embedding_model.py`, `VectorStoreError` in
`vectorstore/chroma.py`, `LLMGenerationError` in `llm/gemini.py`,
`ServiceError` in `services/*`) - that's deliberate: a reader looking at
`chroma.py` should see everything that can go wrong with the vector
store without having to also open this file.

What belongs here instead is:
  - `AIEngineError`: a common ancestor so a caller at the very top of the
    stack (e.g. a future FastAPI exception handler) can catch "anything
    that went wrong inside the AI Engine" with one except clause, without
    needing to enumerate every layer-specific exception type.
  - Exceptions that don't belong to any one layer, such as
    `ConfigurationError` (bad/missing configuration, e.g. a missing API
    key discovered at startup) and `EngineNotInitializedError` (a method
    on `AIEngine` was called before `.initialize()` ran).

Note: existing layer-specific exceptions (`LoaderError`,
`EmbeddingModelError`, etc.) are intentionally NOT retrofitted to inherit
from `AIEngineError` here, to avoid introducing a circular import (this
file would need to import from every other layer). If you want a single
`except AIEngineError` to also catch those, the clean way is to change
each layer's exception to subclass `AIEngineError` directly in that
layer's own file - a small, explicit, one-line change per file, not a
hidden rewiring from here.
"""

from __future__ import annotations


class AIEngineError(Exception):
    """Root exception for engine-level failures that don't belong to any
    single lower layer (configuration problems, lifecycle misuse)."""


class ConfigurationError(AIEngineError):
    """Raised when required configuration is missing or invalid at
    startup (e.g. a required API key is not set in the environment)."""


class EngineNotInitializedError(AIEngineError):
    """Raised when a method on `AIEngine` (chat, summarize, generate_notes,
    generate_quiz, ingest) is called before `AIEngine.initialize()` has
    been run. Initialization loads the embedding model and opens the
    vector store - both required before any engine method can do
    anything useful."""