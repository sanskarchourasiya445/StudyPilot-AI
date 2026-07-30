"""
ai_engine/loaders/base_loader.py

Responsibility: define the single contract every source-specific loader
(PDF, YouTube, TXT, and future DOCX/PPTX/website loaders) must implement.

This is the abstraction that makes "different resources should only have
different loaders" architecturally true. Every module downstream of
loading (preprocessing, embeddings, vector store, retriever, services)
depends ONLY on `BaseLoader` / the `Document` objects it returns - never
on `PDFLoader`, `YouTubeLoader`, or any other concrete class. Adding a
new source type later (e.g. a DOCX loader) means writing one new file
that subclasses `BaseLoader` and registering it in `loader_factory.py` -
no other file in the engine changes.

Why LangChain's `Document` as the shared return type instead of a custom
dataclass?
Every downstream stage (chunker, embedder, Chroma vector store,
retriever) in this engine is built on LangChain primitives, and `Document`
(page_content + metadata dict) is already the exact shape every one of
those stages expects. Inventing a parallel custom type would just mean
converting back and forth at every layer boundary for no benefit.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import List

from langchain_core.documents import Document

logger = logging.getLogger(__name__)


class LoaderError(Exception):
    """Base exception for any failure while loading a source into
    Documents (file not found, unreadable/corrupted content, network
    failure, unsupported format, etc.).

    Concrete loaders should raise a more specific subclass where it adds
    real value (see `PDFLoadError`, `YouTubeLoadError`, `TXTLoadError` in
    their respective files), but every subclass ultimately IS a
    `LoaderError` - so callers (e.g. `loader_factory.py`, `engine.py`)
    only ever need to catch this one type to handle "loading failed",
    regardless of which source type was being loaded.
    """


class BaseLoader(ABC):
    """Abstract interface for turning one source into a list of
    LangChain `Document` objects.

    A loader is constructed with the raw `source` string (a file path or
    a URL) and does nothing until `.load()` is called - this keeps
    construction cheap and side-effect-free, which matters for
    `loader_factory.py`, which may need to ask several loader classes
    "can you handle this source?" before picking one, without triggering
    any I/O as a side effect of just asking.
    """

    def __init__(self, source: str) -> None:
        """Store the raw source reference.

        Args:
            source: A file path (PDF/TXT) or a URL (YouTube). Concrete
            loaders are responsible for validating and interpreting this
            string in whatever way makes sense for their source type.
        """
        if not source or not source.strip():
            raise LoaderError("Loader source must be a non-empty string.")
        self.source = source.strip()

    @classmethod
    @abstractmethod
    def can_handle(cls, source: str) -> bool:
        """Return True if this loader is able to process the given
        source string.

        This is what lets `loader_factory.py` auto-detect the correct
        loader for a source (e.g. a `youtube.com`/`youtu.be` URL routes
        to `YouTubeLoader`, a `.pdf` path routes to `PDFLoader`) without
        the caller having to specify the source type explicitly.

        Implementations must be side-effect-free (no file I/O, no
        network calls) - this is purely a string-shape / extension
        check, so calling it on many loader classes to find a match is
        always cheap and safe.
        """
        raise NotImplementedError

    @abstractmethod
    def load(self) -> List[Document]:
        """Load the source and return it as a list of Documents.

        Each returned `Document` should carry, at minimum, a
        `source_type` and `source` entry in its metadata (e.g.
        `{"source_type": "pdf", "source": "handbook.pdf"}`) so that
        later stages (chunking, retrieval, service layer) can always
        trace an answer back to where it came from, regardless of which
        loader produced it.

        Raises:
            LoaderError: on any failure to load the source (or a more
            specific subclass of it). Callers should only ever need to
            catch `LoaderError` to handle "this source could not be
            loaded", regardless of source type.
        """
        raise NotImplementedError

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"{self.__class__.__name__}(source={self.source!r})"