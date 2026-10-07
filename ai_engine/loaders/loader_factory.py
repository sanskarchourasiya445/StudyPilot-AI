"""
ai_engine/loaders/loader_factory.py

Responsibility: the ONLY place in the engine that knows about every
concrete loader class. This is what makes "different resources should
only have different loaders" true at the call-site level too - callers
(namely `engine.py`) call `load_source(source)` with a raw path or URL
and get back `Document`s, without ever importing `PDFLoader`,
`YouTubeLoader`, or `TXTLoader` themselves.

Adding a new source type later (DOCX, PPTX, a website URL) means:
  1. Write `ai_engine/loaders/docx_loader.py` subclassing `BaseLoader`.
  2. Add its class to `_LOADER_REGISTRY` below.
No other file in the engine changes.
"""

from __future__ import annotations

import logging
from typing import List, Type

from langchain_core.documents import Document

from ai_engine.loaders.base_loader import BaseLoader, LoaderError
from ai_engine.loaders.pdf_loader import PDFLoader
from ai_engine.loaders.txt_loader import TXTLoader
from ai_engine.loaders.youtube_loader import YouTubeLoader
from ai_engine.utils.exceptions import UnsupportedSourceError

logger = logging.getLogger(__name__)

# Order matters only in that the first loader whose `can_handle()`
# returns True wins. Each loader's `can_handle()` is specific enough
# (URL host check, file extension check) that ordering doesn't actually
# create ambiguity today, but YouTubeLoader is listed first since URL
# checks are cheaper than filesystem stat calls.
_LOADER_REGISTRY: List[Type[BaseLoader]] = [YouTubeLoader, PDFLoader, TXTLoader]


def get_loader(source: str) -> BaseLoader:
    """Return an instantiated loader capable of handling `source`.

    Args:
        source: a file path (PDF/TXT) or URL (YouTube).

    Raises:
        UnsupportedSourceError: if no registered loader recognizes the
        source (unsupported file type, malformed URL, non-YouTube video
        link, etc.).
    """
    for loader_cls in _LOADER_REGISTRY:
        if loader_cls.can_handle(source):
            logger.debug("Routing source %r to %s.", source, loader_cls.__name__)
            return loader_cls(source)

    raise UnsupportedSourceError(
        f"No loader registered for source: {source!r}. "
        f"Supported: YouTube URLs, .pdf files, .txt files."
    )


def load_source(source: str) -> List[Document]:
    """Convenience one-liner: resolve the correct loader and load it.

    This is the function `engine.py` calls during ingestion - it never
    needs to know which concrete loader class was used.
    """
    loader = get_loader(source)
    return loader.load()