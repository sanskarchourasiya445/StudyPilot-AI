"""
ai_engine/services/notes_service.py

Responsibility: turn an ingested source's content into structured study
notes (bullet-point or Cornell-style).

Why summarize first, then generate notes from the summary, rather than
feeding raw chunks straight into the notes prompt?
Reuses `SummaryService`'s map-reduce logic to first compress
arbitrarily long source material down to something that reliably fits
in one prompt, THEN asks the LLM to restructure that already-coherent
summary into notes. Skipping straight to notes-from-raw-chunks would
mean either re-implementing map-reduce a second time here, or silently
truncating long sources - both worse than reusing what already works.
"""

from __future__ import annotations

import logging
from typing import List

from langchain_core.documents import Document

from ai_engine.config import DEFAULT_NOTES_STYLE
from ai_engine.llm.gemini import GeminiLLM, LLMGenerationError
from ai_engine.llm.prompts import build_notes_prompt
from ai_engine.services.summary_service import SummaryService, SummaryServiceError

logger = logging.getLogger(__name__)

_VALID_STYLES = ("bullet", "cornell")


class NotesServiceError(Exception):
    """Raised when notes generation fails (empty input, invalid style,
    or an underlying LLM/summary failure)."""


class NotesService:
    """Generates structured study notes from a full source document."""

    def __init__(self, llm: GeminiLLM) -> None:
        self._llm = llm
        # Composition, not inheritance: NotesService HAS-A SummaryService
        # to reuse its map-reduce condensation step, rather than
        # duplicating that logic or subclassing it.
        self._summary_service = SummaryService(llm)

    def generate_notes(
        self,
        documents: List[Document],
        style: str = DEFAULT_NOTES_STYLE,
        summary_text: Optional[str] = None,
    ) -> str:
        """Generate study notes for the full content of `documents`.

        Args:
            documents: typically all chunks belonging to one ingested
            source (see `vectorstore.chroma.get_documents_by_source`).
            style: "bullet" or "cornell".
            summary_text: (optional) pre-condensed summary text to reuse,
            bypassing the map-reduce condensation step.

        Raises:
            NotesServiceError: if `documents` is empty (and summary_text is None),
            `style` is invalid, or an underlying LLM call fails.
        """
        if not documents and not summary_text:
            raise NotesServiceError("Cannot generate notes from an empty document list.")

        if style not in _VALID_STYLES:
            raise NotesServiceError(
                f"Unknown notes style: '{style}'. Must be one of {_VALID_STYLES}."
            )

        if summary_text:
            condensed = summary_text
        else:
            try:
                condensed = self._summary_service.summarize(documents)
            except SummaryServiceError as exc:
                raise NotesServiceError(f"Failed to condense material before note-taking: {exc}") from exc

        logger.info("Generating '%s'-style notes...", style)
        prompt = build_notes_prompt(condensed, style=style)
        try:
            return self._llm.generate(prompt)
        except LLMGenerationError as exc:
            raise NotesServiceError(f"Notes generation failed: {exc}") from exc
