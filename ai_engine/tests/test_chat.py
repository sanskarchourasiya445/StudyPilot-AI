"""
ai_engine/tests/test_chat.py

Unit tests for `services/chat_service.py`, using fake retriever/LLM
objects (not real Chroma, not a real Gemini API key) - this is exactly
what the dependency-injection design in `ChatService.__init__` is for.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from langchain_core.documents import Document

from ai_engine.config import NO_ANSWER_MESSAGE
from ai_engine.llm.gemini import LLMGenerationError
from ai_engine.services.chat_service import ChatService, ChatServiceError


def _make_retriever(documents):
    retriever = MagicMock()
    retriever.invoke.return_value = documents
    return retriever


def _make_llm(response_text: str = "The answer is grounded in the notes."):
    llm = MagicMock()
    llm.generate.return_value = response_text
    return llm


def test_ask_short_circuits_on_zero_retrieved_documents() -> None:
    retriever = _make_retriever([])
    llm = _make_llm()
    service = ChatService(retriever=retriever, llm=llm)

    result = service.ask("What is backpropagation?")

    assert result.was_grounded is False
    assert result.answer == NO_ANSWER_MESSAGE
    assert result.sources == []
    llm.generate.assert_not_called()  # no LLM call should happen at all


def test_ask_returns_grounded_answer_with_sources() -> None:
    docs = [
        Document(page_content="Backprop computes gradients via the chain rule.", metadata={"source": "lecture1.pdf"}),
    ]
    retriever = _make_retriever(docs)
    llm = _make_llm("Backpropagation uses the chain rule to compute gradients.")
    service = ChatService(retriever=retriever, llm=llm)

    result = service.ask("What is backpropagation?")

    assert result.was_grounded is True
    assert result.sources == docs
    assert "chain rule" in result.answer
    llm.generate.assert_called_once()


def test_ask_raises_on_empty_question() -> None:
    service = ChatService(retriever=_make_retriever([]), llm=_make_llm())

    with pytest.raises(ChatServiceError):
        service.ask("   ")


def test_ask_wraps_llm_generation_failure() -> None:
    docs = [Document(page_content="Some content.", metadata={"source": "notes.txt"})]
    retriever = _make_retriever(docs)
    llm = MagicMock()
    llm.generate.side_effect = LLMGenerationError("API rate limit exceeded")
    service = ChatService(retriever=retriever, llm=llm)

    with pytest.raises(ChatServiceError):
        service.ask("What happened?")


def test_ask_wraps_retriever_failure() -> None:
    retriever = MagicMock()
    retriever.invoke.side_effect = RuntimeError("vector store connection lost")
    service = ChatService(retriever=retriever, llm=_make_llm())

    with pytest.raises(ChatServiceError):
        service.ask("What happened?")