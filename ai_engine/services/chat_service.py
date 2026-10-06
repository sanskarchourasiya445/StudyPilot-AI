"""
ai_engine/services/chat_service.py

Responsibility: answer a student's question grounded in retrieved
context (retrieve -> prompt -> generate). This is the "chat with your
study materials" feature.

Two-layer grounding guard (deliberate, not redundant):
  1. If retrieval returns literally zero chunks, short-circuit BEFORE
     calling the LLM at all - saves a network call/cost and is an
     unambiguous "nothing to answer from" case (e.g. an empty workspace,
     or a `source_filter` that matches nothing).
  2. If chunks come back but are low-relevance, we still let the LLM's
     grounded prompt (`llm/prompts.build_rag_prompt`) make the final
     call, because "looks irrelevant" is a fuzzy judgment best made by
     the model that can actually read the content, not a hardcoded
     similarity-score threshold that would need constant re-tuning.

Constructed with its `retriever` and `llm` as explicit dependencies
(dependency injection) rather than reaching into `vectorstore`/`llm`
modules internally - this is what makes `tests/test_chat.py` able to
test the grounding logic with fake retriever/LLM objects, no real
vector store or API key required.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import List, Optional

from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever

from ai_engine.config import NO_ANSWER_MESSAGE
from ai_engine.llm.gemini import GeminiLLM, LLMGenerationError
from ai_engine.llm.prompts import build_query_rewrite_prompt, build_rag_prompt

logger = logging.getLogger(__name__)

_PRONOUN_PATTERN = re.compile(
    r"\b(it|its|they|them|their|theirs|this|that|these|those|he|she|him|her|his)\b",
    re.IGNORECASE,
)

_CONTINUATION_PATTERN = re.compile(
    r"\b(difference|differences|compare|comparison|versus|vs|advantage|advantages|"
    r"disadvantage|disadvantages|pro|pros|con|cons|benefit|benefits|drawback|drawbacks|"
    r"explain further|elaborate|tell me more|more details|what about|how about|"
    r"why is that|why so|the former|the latter|above|previous|another example|"
    r"give an example|examples|both|either|neither)\b",
    re.IGNORECASE,
)


class ChatServiceError(Exception):
    """Raised when answering a question fails for a reason other than
    "nothing was retrieved" (e.g. the LLM call itself failed)."""


@dataclass
class ChatResult:
    """Everything a caller (console, or later a FastAPI response) needs
    to render a chat turn: the answer, the chunks that grounded it, and
    whether an answer was actually attempted or short-circuited."""

    answer: str
    sources: List[Document] = field(default_factory=list)
    was_grounded: bool = True
    retrieval_query: str = ""


class ChatService:
    """Answers questions against a configured retriever, using Gemini."""

    def __init__(self, retriever: VectorStoreRetriever, llm: GeminiLLM) -> None:
        self._retriever = retriever
        self._llm = llm

    @staticmethod
    def _needs_contextual_rewrite(question: str, history: Optional[List[dict]] = None) -> bool:
        """Classify whether a user query requires contextual rewriting
        before retrieval.

        Rules:
        - If history is empty, no prior conversation exists to depend on -> False (0ms, 0 tokens).
        - If query is very short (<= 4 words), e.g., "Why?", "What about differences?",
          "How does it work?", "Definitions?" -> True.
        - If query contains anaphoric pronouns or demonstratives (it, its, they, this, that, etc.) -> True.
        - If query contains continuation triggers (difference, compare, advantages, explain further, etc.) -> True.
        - Otherwise, treat as self-contained -> False.
        """
        if not history:
            return False

        clean_q = question.strip()
        words = clean_q.split()
        if len(words) <= 4:
            return True

        if _PRONOUN_PATTERN.search(clean_q):
            return True

        if _CONTINUATION_PATTERN.search(clean_q):
            return True

        return False

    def _resolve_search_query(self, question: str, history: Optional[List[dict]] = None) -> str:
        """Resolve the query to be sent to vector retrieval.

        If the question is determined to be a conversational follow-up,
        invokes the LLM to rewrite it into a standalone query using recent
        conversation turns. Always falls back to the original question on
        any error or empty response.
        """
        if not self._needs_contextual_rewrite(question, history):
            return question

        try:
            prompt = build_query_rewrite_prompt(question, history)
            rewritten = self._llm.generate(prompt, temperature=0.0)
            if rewritten and rewritten.strip():
                clean_rewritten = rewritten.strip().strip('"\'')
                if clean_rewritten:
                    logger.info(
                        "Contextual query rewritten: %r -> %r", question, clean_rewritten
                    )
                    return clean_rewritten
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Contextual query rewrite failed (%s), falling back to original query: %r",
                exc,
                question,
            )

        return question

    def ask(self, question: str, history: Optional[List[dict]] = None) -> ChatResult:
        """Answer one question.

        Args:
            question: the student's question. The retriever passed at
            construction time already encodes any `source_filter` -
            see `vectorstore.retriever.build_retriever` - so this method
            doesn't need its own filtering parameter.
            history: optional recent conversation history turns.

        Raises:
            ChatServiceError: if retrieval or generation fails for a
            reason other than "zero chunks retrieved" (see class
            docstring for why that specific case is not an error).
        """
        if not question or not question.strip():
            raise ChatServiceError("Question must be a non-empty string.")

        search_query = self._resolve_search_query(question, history)

        try:
            documents = self._retriever.invoke(search_query)
        except Exception as exc:  # noqa: BLE001
            raise ChatServiceError(f"Retrieval failed: {exc}") from exc

        # Layer 1 guard: zero retrieved chunks -> short-circuit, no LLM call.
        if not documents:
            logger.warning(
                "No documents retrieved for question %r (retrieval_query: %r)",
                question,
                search_query,
            )
            return ChatResult(
                answer=NO_ANSWER_MESSAGE,
                sources=[],
                was_grounded=False,
                retrieval_query=search_query,
            )

        prompt = build_rag_prompt(question=question, documents=documents, history=history)

        try:
            answer = self._llm.generate(prompt)
        except LLMGenerationError as exc:
            raise ChatServiceError(f"Answer generation failed: {exc}") from exc

        return ChatResult(
            answer=answer,
            sources=documents,
            was_grounded=True,
            retrieval_query=search_query,
        )
