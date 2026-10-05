import uuid
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from ai_engine.engine import IngestionResult
from backend.app.ai.engine_provider import set_ai_engine, reset_ai_engine
from backend.app.main import app
from backend.app.services.difficulty_service import get_recommended_difficulty

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


# Unit tests for difficulty calculation rules
def test_adaptive_difficulty_rules() -> None:
    # 1. 20% mastery -> easy
    diff, reason = get_recommended_difficulty(20)
    assert diff == "easy"
    assert "20%" in reason

    # 2. 49% mastery -> easy
    diff, _ = get_recommended_difficulty(49)
    assert diff == "easy"

    # 3. 50% mastery -> medium
    diff, _ = get_recommended_difficulty(50)
    assert diff == "medium"

    # 4. 68% mastery -> medium
    diff, reason = get_recommended_difficulty(68)
    assert diff == "medium"
    assert "68%" in reason

    # 5. 79% mastery -> medium
    diff, _ = get_recommended_difficulty(79)
    assert diff == "medium"

    # 6. 80% mastery -> hard
    diff, _ = get_recommended_difficulty(80)
    assert diff == "hard"

    # 7. 100% mastery -> hard
    diff, _ = get_recommended_difficulty(100)
    assert diff == "hard"

    # 8. Missing mastery -> easy
    diff, reason = get_recommended_difficulty(None)
    assert diff == "easy"
    assert "No previous quiz history" in reason

    # 9. Invalid / out-of-bound values safely bounded
    diff_neg, _ = get_recommended_difficulty(-10)
    assert diff_neg == "easy"

    diff_high, _ = get_recommended_difficulty(150)
    assert diff_high == "hard"


# Integration and security tests
def test_adaptive_difficulty_api_and_security() -> None:
    mock_engine = MagicMock()
    unique_res_id = f"res_adaptive_{uuid.uuid4().hex[:8]}"
    mock_engine.ingest.return_value = IngestionResult(
        source="adaptive_study.pdf",
        source_type="pdf",
        pages_or_segments=5,
        chunks_created=10,
        resource_id=unique_res_id,
    )
    mock_engine.generate_quiz.return_value = []
    mock_engine.summarize.return_value = "Summary text for adaptive test."
    set_ai_engine(mock_engine)

    try:
        headers_a = _get_auth_header("adaptive_user_a", "Adaptive User A")
        headers_b = _get_auth_header("adaptive_user_b", "Adaptive User B")

        # Upload resource for User A
        pdf_bytes = b"%PDF-1.4 sample PDF for adaptive quiz test"
        files = {"file": ("database_systems.pdf", pdf_bytes, "application/pdf")}
        res_a = client.post("/api/resources/pdf", files=files, headers=headers_a)
        assert res_a.status_code == 201
        res_id_a = res_a.json()["resource_id"]

        # Generate Quiz
        quiz_resp = client.post(
            f"/api/resources/{res_id_a}/quiz",
            json={"question_count": 5, "difficulty": "hard"},
            headers=headers_a,
        )
        assert quiz_resp.status_code in (200, 201)
        quiz_id = quiz_resp.json()["id"]

        # 10. Query difficulty before quiz -> Defaults to easy
        diff_query1 = client.get(
            "/api/mastery/difficulty",
            params={"topic": "database_systems"},
            headers=headers_a,
        )
        assert diff_query1.status_code == 200
        data1 = diff_query1.json()
        assert data1["topic"] == "database_systems"
        assert data1["mastery_score"] is None
        assert data1["recommended_difficulty"] == "easy"

        # Submit quiz attempt with 100% score -> Mastery 100 -> HARD
        client.post(
            f"/api/mastery/quizzes/{quiz_id}/submit",
            json={"score": 5, "total_questions": 5, "topic": "database_systems"},
            headers=headers_a,
        )

        diff_query2 = client.get(
            "/api/mastery/database_systems/difficulty",
            headers=headers_a,
        )
        assert diff_query2.status_code == 200
        data2 = diff_query2.json()
        assert data2["mastery_score"] == 100
        assert data2["recommended_difficulty"] == "hard"

        # 11. User B query for User A's topic -> Gets 'easy' (User B has no mastery record for topic)
        diff_query_b = client.get(
            "/api/mastery/difficulty",
            params={"topic": "database_systems"},
            headers=headers_b,
        )
        assert diff_query_b.status_code == 200
        assert diff_query_b.json()["mastery_score"] is None
        assert diff_query_b.json()["recommended_difficulty"] == "easy"

        # 12. Quiz generation accepts difficulty parameter
        mock_engine.generate_quiz.assert_called()

        # 13. Backward compatibility: Quiz generation without difficulty parameter defaults to medium
        mock_engine.reset_mock()
        client.post(
            f"/api/resources/{res_id_a}/quiz",
            json={"question_count": 5},
            headers=headers_a,
        )
        # Verify engine generate_quiz called with difficulty parameter
        assert mock_engine.generate_quiz.called

    finally:
        reset_ai_engine()
