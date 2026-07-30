"""
ai_engine/tests/test_summary_cache.py

Unit tests for SummaryCache and AIEngine summary caching / reuse.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from langchain_core.documents import Document

from ai_engine.engine import AIEngine
from ai_engine.utils.summary_cache import SummaryCache, SummaryCacheRecord


def test_summary_cache_basic_ops() -> None:
    cache = SummaryCache()
    assert cache.get("res_1", "hash_a") is None

    cache.set("res_1", "notes.pdf", "Cached summary content", "hash_a")
    rec = cache.get("res_1", "hash_a")
    assert rec is not None
    assert rec.summary == "Cached summary content"
    assert rec.source == "notes.pdf"

    # Invalidate
    assert cache.invalidate("res_1") is True
    assert cache.get("res_1", "hash_a") is None


def test_summary_cache_stale_invalidation() -> None:
    cache = SummaryCache()
    cache.set("res_1", "notes.pdf", "Old summary", "hash_old")

    # Accessing with a different config hash should return None and invalidate
    rec = cache.get("res_1", "hash_new")
    assert rec is None
    assert len(cache) == 0


def _make_initialized_engine() -> AIEngine:
    from ai_engine.services.notes_service import NotesService
    from ai_engine.services.quiz_service import QuizService
    from ai_engine.services.summary_service import SummaryService

    engine = AIEngine()
    engine._initialized = True
    engine._vector_store = MagicMock()
    engine._llm = MagicMock()
    engine._summary_service = SummaryService(engine._llm)
    engine._notes_service = NotesService(engine._llm)
    engine._quiz_service = QuizService(engine._llm)
    return engine


def test_ai_engine_summarize_caches_and_reuses() -> None:
    engine = _make_initialized_engine()
    engine._llm.generate.return_value = "Mocked LLM Summary"

    doc = Document(page_content="Sample text content for summary.", metadata={"source": "test.pdf", "resource_id": "res_100"})
    
    with patch.object(engine, "_get_source_documents", return_value=[doc]):
        # 1st call: cache miss -> calls LLM
        s1 = engine.summarize("test.pdf", resource_id="res_100")
        assert s1 == "Mocked LLM Summary"
        assert engine._llm.generate.call_count == 1

        # 2nd call: cache hit -> 0 extra LLM calls
        s2 = engine.summarize("test.pdf", resource_id="res_100")
        assert s2 == "Mocked LLM Summary"
        assert engine._llm.generate.call_count == 1

        # 3rd call: force_regenerate=True -> forces LLM call
        engine._llm.generate.return_value = "Fresh LLM Summary"
        s3 = engine.summarize("test.pdf", resource_id="res_100", force_regenerate=True)
        assert s3 == "Fresh LLM Summary"
        assert engine._llm.generate.call_count == 2


def test_ai_engine_notes_and_quiz_reuse_cached_summary() -> None:
    engine = _make_initialized_engine()
    engine._llm.generate.side_effect = ["Summary Text", "- Note bullet", '[{"question": "Q?", "options": ["A", "B"], "correct_answer_index": 0, "explanation": "E"}]']

    doc = Document(page_content="Content text.", metadata={"source": "doc.pdf", "resource_id": "res_200"})

    with patch.object(engine, "_get_source_documents", return_value=[doc]):
        # First summarize populates cache (1 LLM call)
        s = engine.summarize("doc.pdf", resource_id="res_200")
        assert s == "Summary Text"
        assert engine._llm.generate.call_count == 1

        # generate_notes reuses cached summary (1 additional LLM call for notes formatting)
        notes = engine.generate_notes("doc.pdf", resource_id="res_200")
        assert notes == "- Note bullet"
        assert engine._llm.generate.call_count == 2

        # generate_quiz reuses cached summary (1 additional LLM call for quiz generation)
        quiz = engine.generate_quiz("doc.pdf", resource_id="res_200")
        assert len(quiz) == 1
        assert engine._llm.generate.call_count == 3


def test_delete_resource_invalidates_cache() -> None:
    engine = AIEngine()
    engine._initialized = True
    engine._vector_store = MagicMock()

    engine._summary_cache.set("res_300", "file.pdf", "Cached text", "hash")
    assert engine._summary_cache.get("res_300", "hash") is not None

    with patch("ai_engine.engine.delete_by_resource_id", return_value=5):
        deleted = engine.delete_resource("res_300")
        assert deleted == 5
        assert engine._summary_cache.get("res_300", "hash") is None
