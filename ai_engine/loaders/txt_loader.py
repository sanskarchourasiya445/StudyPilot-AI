"""
ai_engine/loaders/txt_loader.py

Responsibility: turn one TXT file on disk into LangChain `Document`
objects (one containing the entire file text), with metadata enriched enough
for later stages (chunking, retrieval, service layer) to know which file
the text came from.
"""

from __future__ import annotations

import datetime as _dt
import logging
from pathlib import Path
from typing import List

from langchain_core.documents import Document

from ai_engine.loaders.base_loader import BaseLoader, LoaderError
from ai_engine.utils.helpers import is_valid_file_path_extension

logger = logging.getLogger(__name__)

TXT_EXTENSIONS = (".txt",)


class TXTLoadError(LoaderError):
    """Raised when a TXT file cannot be read (missing file, corrupted,
    or reading error)."""


class TXTLoader(BaseLoader):
    """Loads a single TXT file into a `Document` object.

    Each returned Document's metadata includes:
      - source_type: always "txt"
      - source: the TXT's filename (not the full path)
      - ingested_at: UTC ISO-8601 timestamp of when this load ran
    """

    @classmethod
    def can_handle(cls, source: str) -> bool:
        """True if `source` looks like a path to an existing `.txt` file."""
        if not is_valid_file_path_extension(source, TXT_EXTENSIONS):
            return False
        return Path(source).is_file()

    def load(self) -> List[Document]:
        """Load the TXT file and return it as a Document.

        Raises:
            TXTLoadError: if the file is missing or unreadable.
        """
        file_path = Path(self.source)

        if not file_path.is_file():
            raise TXTLoadError(f"TXT file does not exist: {file_path}")

        try:
            logger.info("Loading TXT: %s", file_path.name)
            # Read text with utf-8 encoding by default, fallback to cp1252/latin-1 if needed
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            raise TXTLoadError(f"Failed to load '{file_path.name}': {exc}") from exc

        if not content.strip():
            raise TXTLoadError(f"'{file_path.name}' is empty or contains only whitespace.")

        ingested_at = _dt.datetime.now(_dt.timezone.utc).isoformat()
        doc = Document(
            page_content=content,
            metadata={
                "source_type": "txt",
                "source": file_path.name,
                "ingested_at": ingested_at,
            }
        )

        logger.info("Loaded text from %s", file_path.name)
        return [doc]