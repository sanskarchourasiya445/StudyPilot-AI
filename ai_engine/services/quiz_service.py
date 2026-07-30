"""
ai_engine/services/quiz_service.py

Responsibility: generate a structured, machine-readable multiple-choice
quiz from an ingested source's content.

Why parse the LLM's output into a typed `QuizQuestion` dataclass instead
of just returning the raw string?
A quiz is meant to be rendered as interactive UI (radio buttons, an
"is this correct" check) by whatever consumes this engine (eventually a
React frontend) - a flat string of question text is far less useful to
that consumer than a parsed structure with `options` as a list and
`correct_answer_index` as an int. Parsing here means the whole rest of
the engine (and its future FastAPI layer) never has to think about
"is Gemini's JSON well-formed" - that concern is fully contained in
this one file.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import List

from langchain_core.documents import Document

from ai_engine.config import DEFAULT_QUIZ_QUESTION_COUNT, QUIZ_DIFFICULTY_LEVELS
from ai_engine.llm.gemini import GeminiLLM, LLMGenerationError
from ai_engine.llm.prompts import build_quiz_prompt
from ai_engine.services.summary_service import SummaryService, SummaryServiceError
from ai_engine.utils.helpers import strip_code_fences

logger = logging.getLogger(__name__)


class QuizServiceError(Exception):
    """Raised when quiz generation fails (empty input, invalid
    parameters, an LLM failure, or the LLM's response could not be
    parsed as the expected JSON shape)."""


@dataclass
class QuizQuestion:
    """One parsed, validated multiple-choice quiz question."""

    question: str
    options: List[str]
    correct_answer_index: int
    explanation: str


class QuizService:
    """Generates a multiple-choice quiz from a full source document."""

    def __init__(self, llm: GeminiLLM) -> None:
        self._llm = llm
        # Composition: reuse SummaryService's map-reduce condensation so
        # quiz generation works correctly even for source material
        # longer than a single prompt can hold, exactly as
        # NotesService does.
        self._summary_service = SummaryService(llm)

    def generate_quiz(
        self,
        documents: List[Document],
        question_count: int = DEFAULT_QUIZ_QUESTION_COUNT,
        difficulty: str = "medium",
        summary_text: Optional[str] = None,
    ) -> List[QuizQuestion]:
        """Generate `question_count` multiple-choice questions from the
        full content of `documents`.

        Args:
            documents: typically all chunks belonging to one ingested
            source.
            question_count: how many questions to generate. Must be > 0.
            difficulty: one of `config.QUIZ_DIFFICULTY_LEVELS`.
            summary_text: (optional) pre-condensed summary text to reuse,
            bypassing the map-reduce condensation step.

        Raises:
            QuizServiceError: for empty input (and summary_text is None), invalid parameters,
            underlying LLM/summarization failure, or a response that
            cannot be parsed into the expected question shape.
        """
        if not documents and not summary_text:
            raise QuizServiceError("Cannot generate a quiz from an empty document list.")

        if question_count <= 0:
            raise QuizServiceError(f"question_count must be positive, got {question_count}.")

        if difficulty not in QUIZ_DIFFICULTY_LEVELS:
            raise QuizServiceError(
                f"Unknown difficulty: '{difficulty}'. Must be one of {QUIZ_DIFFICULTY_LEVELS}."
            )

        if summary_text:
            condensed = summary_text
        else:
            try:
                condensed = self._summary_service.summarize(documents)
            except SummaryServiceError as exc:
                raise QuizServiceError(f"Failed to condense material before quiz generation: {exc}") from exc

        logger.info("Generating %d %s-difficulty quiz question(s)...", question_count, difficulty)
        prompt = build_quiz_prompt(condensed, question_count=question_count, difficulty=difficulty)

        try:
            raw_response = self._llm.generate(prompt)
        except LLMGenerationError as exc:
            raise QuizServiceError(f"Quiz generation failed: {exc}") from exc

        return self._parse_quiz_response(raw_response)

    @staticmethod
    def _parse_quiz_response(raw_response: str) -> List[QuizQuestion]:
        """Parse and validate the LLM's JSON response into
        `QuizQuestion` objects.

        Raises:
            QuizServiceError: if the response is not valid JSON, is not
            a list, or any element is missing required fields / has an
            out-of-range `correct_answer_index`.
        """
        cleaned = strip_code_fences(raw_response)

        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise QuizServiceError(
                f"Gemini's quiz response was not valid JSON: {exc}. "
                f"Raw response: {raw_response[:200]}..."
            ) from exc

        if not isinstance(parsed, list) or not parsed:
            raise QuizServiceError("Gemini's quiz response was not a non-empty JSON array.")

        questions: List[QuizQuestion] = []
        for i, item in enumerate(parsed):
            try:
                options = list(item["options"])
                correct_index = int(item["correct_answer_index"])
                if not (0 <= correct_index < len(options)):
                    raise ValueError(
                        f"correct_answer_index {correct_index} out of range for "
                        f"{len(options)} option(s)."
                    )
                questions.append(
                    QuizQuestion(
                        question=str(item["question"]),
                        options=options,
                        correct_answer_index=correct_index,
                        explanation=str(item.get("explanation", "")),
                    )
                )
            except (KeyError, TypeError, ValueError) as exc:
                raise QuizServiceError(
                    f"Quiz question {i} had an invalid shape: {exc}. Item: {item!r}"
                ) from exc

        logger.info("Parsed %d quiz question(s) successfully.", len(questions))
        return questions
