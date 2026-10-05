import uuid
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from ai_engine.engine import IngestionResult
from backend.app.ai.engine_provider import set_ai_engine, reset_ai_engine
from backend.app.main import app

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


def test_mastery_tracking_and_knowledge_gap_security() -> None:
    mock_engine = MagicMock()
    unique_res_id = f"res_mastery_{uuid.uuid4().hex[:8]}"
    mock_engine.ingest.return_value = IngestionResult(
        source="test_mastery.pdf",
        source_type="pdf",
        pages_or_segments=5,
        chunks_created=10,
        resource_id=unique_res_id,
    )
    mock_engine.generate_quiz.return_value = []
    mock_engine.summarize.return_value = "Mock summary text for test resource."
    set_ai_engine(mock_engine)

    try:
        # 1. Setup User A and User B
        headers_a = _get_auth_header("mastery_user_a", "Mastery User A")
        headers_b = _get_auth_header("mastery_user_b", "Mastery User B")

        # 2. User A uploads a resource & generates a quiz
        pdf_bytes = b"%PDF-1.4 sample PDF for mastery tracking"
        files = {"file": ("data_structures.pdf", pdf_bytes, "application/pdf")}
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

        # 3. User A submits Quiz Attempt 1 (Score: 2/5 -> 40%)
        sub1 = client.post(
            f"/api/mastery/quizzes/{quiz_id}/submit",
            json={"score": 2, "total_questions": 5, "topic": "Data Structures"},
            headers=headers_a,
        )
        assert sub1.status_code == 200
        data1 = sub1.json()
        assert data1["score"] == 2
        assert data1["percentage"] == 40.0
        assert data1["mastery_score"] == 40
        assert data1["mastery_status"] == "Needs Practice"

        # 4. User A submits Quiz Attempt 2 (Score: 5/5 -> 100%)
        # Weighted formula: round(0.6 * 40 + 0.4 * 100) = round(24 + 40) = 64
        sub2 = client.post(
            f"/api/mastery/quizzes/{quiz_id}/submit",
            json={"score": 5, "total_questions": 5, "topic": "Data Structures"},
            headers=headers_a,
        )
        assert sub2.status_code == 200
        data2 = sub2.json()
        assert data2["mastery_score"] == 64
        assert data2["mastery_status"] == "Needs Practice"

        # 5. User A submits Quiz Attempt 3 (Score: 5/5 -> 100%)
        # Weighted formula: round(0.6 * 64 + 0.4 * 100) = round(38.4 + 40) = 78
        sub3 = client.post(
            f"/api/mastery/quizzes/{quiz_id}/submit",
            json={"score": 5, "total_questions": 5, "topic": "Data Structures"},
            headers=headers_a,
        )
        assert sub3.status_code == 200
        data3 = sub3.json()
        assert data3["mastery_score"] == 78
        assert data3["mastery_status"] == "Good"

        # 6. Verify GET /api/mastery for User A
        m_list = client.get("/api/mastery", headers=headers_a)
        assert m_list.status_code == 200
        records = m_list.json()
        assert len(records) == 1
        assert records[0]["topic"] == "Data Structures"
        assert records[0]["mastery_score"] == 78

        # 7. Verify GET /api/mastery/gaps for User A (Data Structures score 78 >= 70, so 0 gaps)
        gaps_a = client.get("/api/mastery/gaps", headers=headers_a)
        assert gaps_a.status_code == 200
        assert gaps_a.json()["gaps_count"] == 0

        # 8. User A adds a weak topic ("Algorithms" score 20)
        sub_weak = client.post(
            f"/api/mastery/quizzes/{quiz_id}/submit",
            json={"score": 1, "total_questions": 5, "topic": "Algorithms"},
            headers=headers_a,
        )
        assert sub_weak.status_code == 200
        assert sub_weak.json()["mastery_score"] == 20
        assert sub_weak.json()["mastery_status"] == "Needs Attention"

        # 9. Verify GET /api/mastery/gaps returns "Algorithms" gap
        gaps_a2 = client.get("/api/mastery/gaps", headers=headers_a)
        assert gaps_a2.status_code == 200
        g_data = gaps_a2.json()
        assert g_data["gaps_count"] == 1
        assert g_data["gaps"][0]["topic"] == "Algorithms"

        # 10. SECURITY ISOLATION: User B gets /api/mastery -> 0 records (cannot view User A's data)
        m_list_b = client.get("/api/mastery", headers=headers_b)
        assert m_list_b.status_code == 200
        assert len(m_list_b.json()) == 0

        # 11. SECURITY ISOLATION: User B tries to submit quiz for User A's resource -> 404 Not Found
        cross_sub = client.post(
            f"/api/mastery/quizzes/{quiz_id}/submit",
            json={"score": 5, "total_questions": 5},
            headers=headers_b,
        )
        assert cross_sub.status_code == 404

    finally:
        reset_ai_engine()
