import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from ai_engine.engine import IngestionResult
from backend.app.ai.engine_provider import set_ai_engine, reset_ai_engine
from backend.app.main import app
from backend.app.services.revision_service import (
    get_review_interval,
    calculate_next_review_at,
    get_revision_status,
)

client = TestClient(app)


def _get_auth_header(prefix: str, name: str) -> dict:
    unique_email = f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"
    reg = client.post(
        "/api/auth/register",
        json={"email": unique_email, "password": "password123", "name": name},
    )
    assert reg.status_code == 201
    login = client.post(
        "/api/auth/login",
        json={"email": unique_email, "password": "password123"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# 1 - 13: Unit tests for interval and status logic
def test_revision_interval_rules_and_status() -> None:
    # 1. 20% -> 1 day
    assert get_review_interval(20) == 1
    # 2. 39% -> 1 day
    assert get_review_interval(39) == 1

    # 3. 40% -> 3 days
    assert get_review_interval(40) == 3
    # 4. 69% -> 3 days
    assert get_review_interval(69) == 3

    # 5. 70% -> 7 days
    assert get_review_interval(70) == 7
    # 6. 84% -> 7 days
    assert get_review_interval(84) == 7

    # 7. 85% -> 14 days
    assert get_review_interval(85) == 14
    # 8. 100% -> 14 days
    assert get_review_interval(100) == 14

    # 9. next_review_at timestamp calculation
    base_time = datetime(2026, 8, 26, 12, 0, 0, tzinfo=timezone.utc)
    next_rev = calculate_next_review_at(55, base_time=base_time)
    assert next_rev == datetime(2026, 8, 29, 12, 0, 0, tzinfo=timezone.utc)

    # 10. Scheduled status logic (current < next_review_at)
    future_time = base_time + timedelta(days=2)
    assert get_revision_status(future_time, current_time=base_time) == "Scheduled"

    # 11. Due status logic (current >= next_review_at)
    past_time = base_time - timedelta(hours=1)
    assert get_revision_status(past_time, current_time=base_time) == "Due"

    # 12. Overdue / Due status logic
    very_past = base_time - timedelta(days=5)
    assert get_revision_status(very_past, current_time=base_time) == "Due"

    # 13. Missing next_review_at -> "Not Scheduled"
    assert get_revision_status(None) == "Not Scheduled"


# 14 - 16: Integration & security tests
def test_revision_api_persistence_and_security() -> None:
    mock_engine = MagicMock()
    unique_res_id = f"res_rev_{uuid.uuid4().hex[:8]}"
    mock_engine.ingest.return_value = IngestionResult(
        source="revision_notes.pdf",
        source_type="pdf",
        pages_or_segments=5,
        chunks_created=10,
        resource_id=unique_res_id,
    )
    mock_engine.generate_quiz.return_value = []
    mock_engine.summarize.return_value = "Summary for revision test."
    set_ai_engine(mock_engine)

    try:
        headers_a = _get_auth_header("rev_user_a", "Revision User A")
        headers_b = _get_auth_header("rev_user_b", "Revision User B")

        # User A uploads a resource & creates a quiz
        pdf_bytes = b"%PDF-1.4 sample PDF for revision scheduler"
        files = {"file": ("operating_systems.pdf", pdf_bytes, "application/pdf")}
        res_a = client.post("/api/resources/pdf", files=files, headers=headers_a)
        assert res_a.status_code == 201
        res_id_a = res_a.json()["resource_id"]

        quiz_resp = client.post(
            f"/api/resources/{res_id_a}/quiz",
            json={"question_count": 5, "difficulty": "medium"},
            headers=headers_a,
        )
        assert quiz_resp.status_code in (200, 201)
        quiz_id = quiz_resp.json()["id"]

        # 14. Quiz submission creates/updates revision schedule (Score 2/5 -> 40% -> 3 days review)
        sub = client.post(
            f"/api/mastery/quizzes/{quiz_id}/submit",
            json={"score": 2, "total_questions": 5, "topic": "Operating Systems"},
            headers=headers_a,
        )
        assert sub.status_code == 200
        data = sub.json()
        assert data["review_interval_days"] == 3
        assert data["next_review_at"] is not None

        # 15. Revision schedule persists in PostgreSQL and is queryable via GET /api/revision
        rev_list = client.get("/api/revision", headers=headers_a)
        assert rev_list.status_code == 200
        items = rev_list.json()
        assert len(items) == 1
        assert items[0]["topic"] == "Operating Systems"
        assert items[0]["review_interval_days"] == 3
        assert items[0]["status"] == "Scheduled"
        assert items[0]["resource_id"] == res_id_a

        # 16. User B cannot access User A's revision schedule (User B gets 0 items)
        rev_list_b = client.get("/api/revision", headers=headers_b)
        assert rev_list_b.status_code == 200
        assert len(rev_list_b.json()) == 0

    finally:
        reset_ai_engine()
