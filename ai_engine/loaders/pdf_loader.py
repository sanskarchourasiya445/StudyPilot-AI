"""
ai_engine/loaders/pdf_loader.py

Responsibility: turn one PDF file on disk into LangChain `Document`
objects (one per page), with metadata enriched enough for later stages
(chunking, retrieval, service layer) to always know which file and page
a piece of text came from.

This file knows nothing about chunking, embeddings, or the vector store
- it only knows how to read one PDF. That separation is what lets
`loaders/loader_factory.py` treat every loader identically.
"""

from __future__ import annotations

import datetime as _dt
import logging
from pathlib import Path
from typing import List

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document

from ai_engine.loaders.base_loader import BaseLoader, LoaderError
from ai_engine.utils.helpers import is_valid_file_path_extension

logger = logging.getLogger(__name__)

PDF_EXTENSIONS = (".pdf",)


class PDFLoadError(LoaderError):
    """Raised when a PDF cannot be read (missing file, corrupted,
    encrypted without a supplied password, zero extractable pages)."""


class PDFLoader(BaseLoader):
    """Loads a single PDF file into per-page `Document` objects.

    Each returned Document's metadata includes:
      - source_type: always "pdf"
      - source: the PDF's filename (not the full path, so citations
        shown to end users don't leak local filesystem layout)
      - page: 0-indexed page number (set by LangChain's PyPDFLoader)
      - ingested_at: UTC ISO-8601 timestamp of when this load ran
    """

    @classmethod
    def can_handle(cls, source: str) -> bool:
        """True if `source` looks like a path to an existing `.pdf` file.

        Deliberately checks both the extension AND that the file exists,
        so the loader factory can distinguish "this is a PDF path that
        doesn't exist" (a real error the caller should see) from "this
        isn't a PDF at all" (try the next loader).
        """
        if not is_valid_file_path_extension(source, PDF_EXTENSIONS):
            return False
        return Path(source).is_file()

    def load(self) -> List[Document]:
        """Load the PDF and return one Document per page.

        Raises:
            PDFLoadError: if the file is missing, unreadable, or
            produces zero pages (e.g. a scanned-image PDF with no
            extractable text layer).
        """
        file_path = Path(self.source)

        if not file_path.is_file():
            raise PDFLoadError(f"PDF file does not exist: {file_path}")

        try:
            logger.info("Loading PDF: %s", file_path.name)
            loader = PyPDFLoader(str(file_path))
            pages = loader.load()
        except Exception as exc:  # noqa: BLE001 - normalize any pypdf /
            # langchain failure (corrupted file, missing backend,
            # permission error) into our own domain exception, so
            # `loader_factory.py` and `engine.py` only ever need to
            # catch `LoaderError`.
            raise PDFLoadError(f"Failed to load '{file_path.name}': {exc}") from exc

        if not pages:
            raise PDFLoadError(
                f"'{file_path.name}' produced zero pages "
                f"(empty file or scanned-image PDF with no text layer?)."
            )

        ingested_at = _dt.datetime.now(_dt.timezone.utc).isoformat()
        for page in pages:
            # PyPDFLoader already sets metadata["page"] and
            # metadata["source"] (full path) - we enrich rather than
            # overwrite, and add our own normalized "source" (filename
            # only) for consistency with the other loaders.
            page.metadata.update(
                {
                    "source_type": "pdf",
                    "source": file_path.name,
                    "ingested_at": ingested_at,
                }
            )

        logger.info("Loaded %d page(s) from %s", len(pages), file_path.name)
        return pages