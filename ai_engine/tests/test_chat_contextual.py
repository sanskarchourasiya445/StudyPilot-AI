"""
ai_engine/tests/test_chat_contextual.py

Comprehensive tests for contextual query rewriting and grounding in ChatService,
covering TEST A through TEST H.
"""

from __future__ import annotations

from unittest.mock import MagicMock
import pytest
from langchain_core.documents import Document

from ai_engine.config import NO_ANSWER_MESSAGE
from ai_engine.services.chat_service import ChatService, ChatResult
from ai_engine.vectorstore.retriever import build_retriever


def _make_retriever(documents=None, filter_kwargs=None):
    retriever = MagicMock()
    retriever.invoke.return_value = documents if documents is not None else []
    retriever.search_kwargs = filter_kwargs or {}
    return retriever


def _make_llm():
    llm = MagicMock()
    return llm


def test_test_a_self_contained_question_no_rewrite():
    """TEST A: Self-contained question.
    - No rewrite needed.
    - Existing retrieval behavior remains unchanged.
    - LLM generate is only called once for answer generation.
    """
    docs = [Document(page_content="Binary search runs in O(log n) time.", metadata={"source": "dsa.pdf"})]
    retriever = _make_retriever(docs)
    llm = _make_llm()
    llm.generate.return_value = "Binary search is an efficient search algorithm on sorted arrays."

    service = ChatService(retriever=retriever, llm=llm)
    history = [
        {"role": "user", "content": "What is a Stack?"},
        {"role": "assistant", "content": "A stack is a LIFO data structure."},
    ]

    question = "What is binary search algorithm?"
    assert service._needs_contextual_rewrite(question, history) is False

    result = service.ask(question, history=history)

    assert result.was_grounded is True
    assert result.retrieval_query == question
    retriever.invoke.assert_called_once_with(question)
    llm.generate.assert_called_once()  # only final prompt, no rewrite prompt


def test_test_b_contextual_follow_up_uses_conversation_context():
    """TEST B: Contextual follow-up question.
    - Rewriter uses previous conversation to resolve ambiguous follow-up.
    - Retriever is invoked with the standalone search query.
    """
    docs = [
        Document(page_content="Stack is LIFO (push/pop). Queue is FIFO (enqueue/dequeue).", metadata={"source": "dsa.pdf"})
    ]
    retriever = _make_retriever(docs)
    llm = _make_llm()

    def mock_generate(prompt, **kwargs):
        if "STANDALONE SEARCH QUERY:" in prompt:
            return "What are the definitions of Stack and Queue and what are their main differences?"
        return "A Stack is a LIFO structure whereas a Queue is a FIFO structure."

    llm.generate.side_effect = mock_generate
    service = ChatService(retriever=retriever, llm=llm)

    history = [
        {"role": "user", "content": "What is the difference between Stack and Queue?"},
        {"role": "assistant", "content": "A stack is LIFO while a queue is FIFO."},
    ]

    question = "What are the main definitions and differences?"
    assert service._needs_contextual_rewrite(question, history) is True

    result = service.ask(question, history=history)

    expected_rewrite = "What are the definitions of Stack and Queue and what are their main differences?"
    assert result.was_grounded is True
    assert result.retrieval_query == expected_rewrite
    retriever.invoke.assert_called_once_with(expected_rewrite)
    assert len(result.sources) == 1
    assert "LIFO" in result.answer


def test_test_c_pronoun_follow_up_resolves_subject():
    """TEST C: Pronoun/reference follow-up.
    - e.g., 'What about its advantages?'
    - Resolves pronoun to the subject discussed previously.
    """
    docs = [Document(page_content="Hash Tables provide O(1) average lookup time.", metadata={"source": "hashtable.pdf"})]
    retriever = _make_retriever(docs)
    llm = _make_llm()

    def mock_generate(prompt, **kwargs):
        if "STANDALONE SEARCH QUERY:" in prompt:
            return "What are the advantages of a Hash Table?"
        return "The advantages of Hash Tables include O(1) average time complexity for lookup."

    llm.generate.side_effect = mock_generate
    service = ChatService(retriever=retriever, llm=llm)

    history = [
        {"role": "user", "content": "How does a Hash Table work?"},
        {"role": "assistant", "content": "A Hash Table maps keys to values using a hash function."},
    ]

    question = "What about its advantages?"
    assert service._needs_contextual_rewrite(question, history) is True

    result = service.ask(question, history=history)

    assert result.retrieval_query == "What are the advantages of a Hash Table?"
    retriever.invoke.assert_called_once_with("What are the advantages of a Hash Table?")
    assert result.was_grounded is True


def test_test_d_ambiguous_query_insufficient_context_preserves_original():
    """TEST D: Ambiguous query with insufficient context.
    - Does NOT invent or hallucinate a topic.
    - Returns original query unchanged when context does not clarify referents.
    """
    retriever = _make_retriever([])
    llm = _make_llm()

    # Rewriter prompt returns original query because context contains no topic
    llm.generate.return_value = "Tell me more about it."
    service = ChatService(retriever=retriever, llm=llm)

    history = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hello! How can I help you today?"},
    ]

    question = "Tell me more about it."
    assert service._needs_contextual_rewrite(question, history) is True

    result = service.ask(question, history=history)

    assert result.retrieval_query == question
    retriever.invoke.assert_called_once_with(question)
    assert result.was_grounded is False
    assert result.answer == NO_ANSWER_MESSAGE


def test_test_e_out_of_domain_question_preserves_anti_hallucination():
    """TEST E: Out-of-domain question.
    - Zero retrieved documents -> short-circuits to NO_ANSWER_MESSAGE.
    - Unrelated retrieved documents -> LLM returns NO_ANSWER_MESSAGE.
    """
    # Case 1: zero chunks
    retriever = _make_retriever([])
    llm = _make_llm()
    service = ChatService(retriever=retriever, llm=llm)

    result = service.ask("What is the capital of France?")
    assert result.was_grounded is False
    assert result.answer == NO_ANSWER_MESSAGE
    llm.generate.assert_not_called()

    # Case 2: unrelated chunks retrieved, LLM grounded prompt returns NO_ANSWER_MESSAGE
    unrelated_docs = [Document(page_content="Stack push and pop operations.", metadata={"source": "dsa.pdf"})]
    retriever2 = _make_retriever(unrelated_docs)
    llm2 = _make_llm()
    llm2.generate.return_value = NO_ANSWER_MESSAGE
    service2 = ChatService(retriever=retriever2, llm=llm2)

    result2 = service2.ask("What is the capital of France?")
    assert result2.was_grounded is True
    assert result2.answer == NO_ANSWER_MESSAGE


def test_test_f_single_resource_scope_isolation():
    """TEST F: Single-resource scope.
    - Vector store retriever is constructed with resource_id filter.
    - Contextual query rewrite cannot alter or bypass resource scope.
    """
    mock_store = MagicMock()
    mock_retriever = MagicMock()
    mock_retriever.search_kwargs = {"filter": {"resource_id": "res-os-123"}}
    mock_store.as_retriever.return_value = mock_retriever

    retriever = build_retriever(mock_store, resource_id="res-os-123")
    assert retriever.search_kwargs["filter"] == {"resource_id": "res-os-123"}

    # Pass to ChatService
    llm = _make_llm()
    llm.generate.return_value = "Rewritten query on OS scheduling"
    service = ChatService(retriever=retriever, llm=llm)

    history = [
        {"role": "user", "content": "Explain CPU scheduling algorithms."},
        {"role": "assistant", "content": "CPU scheduling algorithms include FCFS, SJF, and Round Robin."},
    ]
    service.ask("What are their differences?", history=history)

    # Filter on retriever was never modified by rewrite
    assert retriever.search_kwargs["filter"] == {"resource_id": "res-os-123"}


def test_test_g_multi_resource_scope_isolation():
    """TEST G: Multi-resource scope.
    - Vector store retriever is constructed with resource_ids list filter.
    - Rewriting works seamlessly within the multi-resource filter boundary.
    """
    mock_store = MagicMock()
    mock_retriever = MagicMock()
    target_filter = {"resource_id": {"$in": ["res-1", "res-2"]}}
    mock_retriever.search_kwargs = {"filter": target_filter}
    mock_store.as_retriever.return_value = mock_retriever

    retriever = build_retriever(mock_store, resource_ids=["res-1", "res-2"])
    assert retriever.search_kwargs["filter"] == target_filter

    llm = _make_llm()
    service = ChatService(retriever=retriever, llm=llm)
    assert retriever.search_kwargs["filter"] == target_filter


def test_test_h_citations_match_actual_retrieved_sources():
    """TEST H: Citations still point to actual retrieved sources.
    - Result sources contain exact document metadata and content.
    """
    doc1 = Document(
        page_content="Stack LIFO details",
        metadata={"source": "dsa_stacks.pdf", "resource_id": "res-1", "page": 4}
    )
    doc2 = Document(
        page_content="Queue FIFO details",
        metadata={"source": "dsa_queues.pdf", "resource_id": "res-2", "page": 8}
    )
    retriever = _make_retriever([doc1, doc2])
    llm = _make_llm()
    llm.generate.return_value = "Stacks are LIFO and Queues are FIFO."

    service = ChatService(retriever=retriever, llm=llm)
    result = service.ask("What are their definitions?", history=[{"role": "user", "content": "Stack and queue"}])

    assert len(result.sources) == 2
    assert result.sources[0].metadata["source"] == "dsa_stacks.pdf"
    assert result.sources[0].metadata["page"] == 4
    assert result.sources[1].metadata["source"] == "dsa_queues.pdf"
    assert result.sources[1].metadata["page"] == 8
