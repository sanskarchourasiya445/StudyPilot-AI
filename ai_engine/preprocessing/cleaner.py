"""
ai_engine/preprocessing/cleaner.py

Responsibility: normalize raw text extracted by any loader before it
gets chunked and embedded. This runs AFTER loading and BEFORE chunking,
and applies uniformly regardless of source type - a PDF page, a TXT
file, and a YouTube transcript all pass through the same cleaning step,
which is exactly the point of the "everything after text extraction
should be shared" pipeline design.

Why clean before chunking rather than after?
`RecursiveCharacterTextSplitter` (in `chunker.py`) makes split decisions
based on character positions and separator patterns (paragraph breaks,
sentence boundaries). Messy whitespace/control characters distort those
boundaries - cleaning first means chunk boundaries land on real sentence/
paragraph breaks instead of artifacts of PDF extraction or caption
formatting.
"""

from __future__ import annotations

import logging
import re
from typing import List

from langchain_core.documents import Document

from ai_engine.utils.helpers import clean_whitespace

logger = logging.getLogger(__name__)

# Control characters (excluding common whitespace: \t \n \r) that
# sometimes leak in from PDF text extraction or malformed caption data.
_CONTROL_CHAR_PATTERN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

# Common Whisper/auto-caption filler tokens that add noise without
# adding meaning for retrieval or summarization purposes.
_FILLER_WORD_PATTERN = re.compile(
    r"\b(um+|uh+|erm+|you know|i mean)\b[,.]?", flags=re.IGNORECASE
)


def strip_control_characters(text: str) -> str:
    """Remove non-printable control characters that don't carry
    semantic meaning but can confuse downstream tokenizers/splitters."""
    return _CONTROL_CHAR_PATTERN.sub("", text)


def remove_filler_words(text: str) -> str:
    """Strip common spoken-language filler words.

    This matters specifically for YouTube transcripts (both caption-
    based and Whisper-based) - PDFs and TXT files rarely contain these,
    so applying it universally is harmless (a no-op) but keeps the
    cleaning pipeline uniform across source types rather than branching
    on `source_type` here, which would leak loader-specific concerns into
    a stage that's supposed to be source-agnostic.
    """
    return _FILLER_WORD_PATTERN.sub("", text)


def clean_text(text: str, remove_fillers: bool = True) -> str:
    """Full cleaning pipeline for one piece of text: strip control
    characters, optionally remove filler words, then normalize
    whitespace.

    Args:
        text: raw text to clean.
        remove_fillers: whether to strip spoken-language filler words.
        Defaults to True since it's a safe no-op for written sources.
    """
    text = strip_control_characters(text)
    if remove_fillers:
        text = remove_filler_words(text)
    return clean_whitespace(text)


def clean_documents(documents: List[Document], remove_fillers: bool = True) -> List[Document]:
    """Apply `clean_text` to every Document's `page_content` in place,
    preserving metadata untouched.

    Returns the same list (mutated) rather than a copy, since cleaning
    is a pure content transformation with no need to preserve the
    pre-cleaning text - this avoids doubling memory usage for large
    ingestion batches.
    """
    if not documents:
        logger.warning("clean_documents called with an empty document list.")
        return documents

    empty_after_cleaning = 0
    for doc in documents:
        doc.page_content = clean_text(doc.page_content, remove_fillers=remove_fillers)
        if not doc.page_content:
            empty_after_cleaning += 1

    if empty_after_cleaning:
        logger.warning(
            "%d document(s) became empty after cleaning (likely near-blank "
            "pages or transcript segments).",
            empty_after_cleaning,
        )

    logger.info("Cleaned %d document(s).", len(documents))
    return documents