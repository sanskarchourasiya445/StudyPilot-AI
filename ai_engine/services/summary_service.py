"""
ai_engine/services/summary_service.py

Responsibility: produce a coherent summary of an entire ingested source
(a full PDF, a full lecture transcript), using a map-reduce strategy so
sources longer than a single LLM context window are handled correctly.

Why map-reduce instead of one big prompt?
A full lecture transcript or a multi-chapter PDF can easily exceed a
single prompt's practical size. Map-reduce summarizes large,
summary-sized chunks (`preprocessing.chunker.chunk_documents_for_summary`)
independently first (the "map" step), then combines those partial
summaries into one final summary (the "reduce" step) - this scales to
arbitrarily long source material without hitting context limits, at the
cost of one extra LLM call per chunk.
"""

from __future__ import annotations

import logging
from typing import List

from langchain_core.documents import Document

from ai_engine.llm.gemini import GeminiLLM, LLMGenerationError
from ai_engine.llm.prompts import build_summary_combine_prompt, build_summary_map_prompt
from ai_engine.preprocessing.chunker import chunk_documents_for_summary

logger = logging.getLogger(__name__)


class SummaryServiceError(Exception):
    """Raised when summarization fails (empty input, or an LLM call
    fails at either the map or reduce step)."""


class SummaryService:
    """Summarizes a full source document using map-reduce."""

    def __init__(self, llm: GeminiLLM) -> None:
        self._llm = llm

    def summarize(self, documents: List[Document]) -> str:
        """Summarize the full content of `documents` (typically all
        chunks belonging to one ingested source, fetched via
        `vectorstore.chroma.get_documents_by_source`).

        Raises:
            SummaryServiceError: if `documents` is empty, or if any
            LLM call fails.
        """
        if not documents:
            raise SummaryServiceError("Cannot summarize an empty document list.")

        summary_chunks = chunk_documents_for_summary(documents)
        logger.info("Summarizing %d summary-chunk(s)...", len(summary_chunks))

        chunk_summaries: List[str] = []
        for i, chunk in enumerate(summary_chunks, start=1):
            logger.info("Map step %d/%d...", i, len(summary_chunks))
            prompt = build_summary_map_prompt(chunk.page_content)
            try:
                chunk_summaries.append(self._llm.generate(prompt))
            except LLMGenerationError as exc:
                raise SummaryServiceError(f"Map step failed on chunk {i}: {exc}") from exc

        # If there was only one chunk, the "reduce" step would just be
        # asking the LLM to reformat a single summary it already wrote -
        # skip it and return that summary directly.
        if len(chunk_summaries) == 1:
            return chunk_summaries[0]

        logger.info("Combining %d partial summaries...", len(chunk_summaries))
        combine_prompt = build_summary_combine_prompt(chunk_summaries)
        try:
            return self._llm.generate(combine_prompt)
        except LLMGenerationError as exc:
            raise SummaryServiceError(f"Combine step failed: {exc}") from exc