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
from dataclasses import dataclass, field
from typing import List, Optional

from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever

from ai_engine.config import NO_ANSWER_MESSAGE
from ai_engine.llm.gemini import GeminiLLM, LLMGenerationError
from ai_engine.llm.prompts import build_rag_prompt

logger = logging.getLogger(__name__)


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


class ChatService:
    """Answers questions against a configured retriever, using Gemini."""

    def __init__(self, retriever: VectorStoreRetriever, llm: GeminiLLM) -> None:
        self._retriever = retriever
        self._llm = llm

    def ask(self, question: str) -> ChatResult:
        """Answer one question.

        Args:
            question: the student's question. The retriever passed at
            construction time already encodes any `source_filter` -
            see `vectorstore.retriever.build_retriever` - so this method
            doesn't need its own filtering parameter.

        Raises:
            ChatServiceError: if retrieval or generation fails for a
            reason other than "zero chunks retrieved" (see class
            docstring for why that specific case is not an error).
        """
        if not question or not question.strip():
            raise ChatServiceError("Question must be a non-empty string.")

        try:
            documents = self._retriever.invoke(question)
        except Exception as exc:  # noqa: BLE001
            raise ChatServiceError(f"Retrieval failed: {exc}") from exc

        # Layer 1 guard: zero retrieved chunks -> short-circuit, no LLM call.
        if not documents:
            logger.warning("No documents retrieved for question: %r", question)
            return ChatResult(answer=NO_ANSWER_MESSAGE, sources=[], was_grounded=False)

        prompt = build_rag_prompt(question=question, documents=documents)

        try:
            answer = self._llm.generate(prompt)
        except LLMGenerationError as exc:
            raise ChatServiceError(f"Answer generation failed: {exc}") from exc

        return ChatResult(answer=answer, sources=documents, was_grounded=True)
