"""
ai_engine/preprocessing/chunker.py

Responsibility: split Documents (of any source type - PDF page,
YouTube transcript, TXT file) into retrieval-sized chunks.

Why RecursiveCharacterTextSplitter specifically?
It tries a prioritized list of separators (paragraph -> line -> sentence
-> word -> character) and only falls back to a harder split when a
softer one doesn't fit within chunk_size. This keeps chunks semantically
coherent instead of slicing mid-sentence, which matters both for
retrieval quality (chat) and for summary/notes/quiz generation, which
all depend on chunks being self-contained enough to reason about
individually.

Two chunk sizes are supported (both sourced from `config.py`, never
hardcoded here):
  - CHUNK_SIZE/CHUNK_OVERLAP: small chunks for retrieval (chat), where
    precision matters more than context breadth.
  - SUMMARY_MAP_CHUNK_SIZE/SUMMARY_MAP_CHUNK_OVERLAP: larger chunks for
    the summarization service's map step, where broader context per LLM
    call reduces the number of map calls needed and produces more
    coherent partial summaries.
"""

from __future__ import annotations

import logging
from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from ai_engine.config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    SUMMARY_MAP_CHUNK_OVERLAP,
    SUMMARY_MAP_CHUNK_SIZE,
)

logger = logging.getLogger(__name__)


def build_splitter(chunk_size: int, chunk_overlap: int) -> RecursiveCharacterTextSplitter:
    """Factory for a configured splitter.

    Kept as a function (not a module-level singleton) so callers can
    build splitters with different parameters (retrieval-sized vs
    summary-sized) without mutating any shared global state.
    """
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )


def chunk_documents(
    documents: List[Document],
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> List[Document]:
    """Split documents into retrieval-sized chunks for the vector store.

    LangChain's splitter copies each parent Document's metadata onto
    every resulting chunk automatically, so `source`, `source_type`,
    `page` (for PDFs), and `video_id` (for YouTube) all survive into the
    chunk level without any extra code here.
    """
    if not documents:
        logger.warning("chunk_documents called with an empty document list.")
        return []

    splitter = build_splitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = splitter.split_documents(documents)

    missing_source = [c for c in chunks if "source" not in c.metadata]
    if missing_source:
        logger.error(
            "%d chunk(s) lost 'source' metadata during splitting - "
            "citations for these chunks will show as 'unknown'.",
            len(missing_source),
        )

    logger.info(
        "Split %d document(s) into %d chunk(s) (chunk_size=%d, overlap=%d).",
        len(documents),
        len(chunks),
        chunk_size,
        chunk_overlap,
    )
    return chunks


def chunk_documents_for_summary(documents: List[Document]) -> List[Document]:
    """Split documents into larger, summary-sized chunks.

    Used exclusively by `services/summary_service.py`'s map step - kept
    as a separate named function (rather than requiring every caller to
    remember to pass the summary-specific constants into
    `chunk_documents`) so the intent at each call site is unambiguous.
    """
    return chunk_documents(
        documents,
        chunk_size=SUMMARY_MAP_CHUNK_SIZE,
        chunk_overlap=SUMMARY_MAP_CHUNK_OVERLAP,
    )

def chunk_documents_for_summary(documents: List[Document]) -> List[Document]:
    """Merge documents into continuous text, then split into larger,
    summary-sized chunks."""
    if not documents:
        logger.warning("chunk_documents_for_summary called with an empty document list.")
        return []

    combined_text = "\n\n".join(doc.page_content for doc in documents)
    shared_metadata = dict(documents[0].metadata)

    splitter = build_splitter(
        chunk_size=SUMMARY_MAP_CHUNK_SIZE, chunk_overlap=SUMMARY_MAP_CHUNK_OVERLAP
    )
    texts = splitter.split_text(combined_text)
    summary_chunks = [Document(page_content=text, metadata=dict(shared_metadata)) for text in texts]

    logger.info(
        "Combined %d retrieval chunk(s) into %d summary-sized chunk(s) "
        "(chunk_size=%d, overlap=%d).",
        len(documents), len(summary_chunks), SUMMARY_MAP_CHUNK_SIZE, SUMMARY_MAP_CHUNK_OVERLAP,
    )
    return summary_chunks
