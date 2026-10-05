import uuid
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient
from langchain_core.documents import Document
from ai_engine.engine import IngestionResult, QuizQuestion
from ai_engine.services.chat_service import ChatResult
from backend.app.ai.engine_provider import set_ai_engine, reset_ai_engine
from backend.app.main import app

client = TestClient(app)


def _get_auth_header(prefix: str) -> dict:
    unique_email = f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"
    reg = client.post(
        "/api/auth/register",
        json={"email": unique_email, "password": "password123", "name": f"User {prefix}"},
    )
    assert reg.status_code == 201
    login = client.post(
        "/api/auth/login",
        json={"email": unique_email, "password": "password123"},
    )
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_ai_capabilities_and_security() -> None:
    unique_res_id = f"res_{uuid.uuid4().hex[:8]}"
    mock_engine = MagicMock()
    mock_engine.ingest.return_value = IngestionResult(
        source="doc_a.pdf",
        source_type="pdf",
        pages_or_segments=5,
        chunks_created=10,
        resource_id=unique_res_id,
    )
    doc_chunk = Document(page_content="Sample content text.", metadata={"source": "doc_a.pdf"})
    mock_engine.chat.return_value = ChatResult(
        answer="StudyPilot is a personalized AI study platform.",
        sources=[doc_chunk],
    )
    mock_engine.ask.return_value = mock_engine.chat.return_value
    mock_engine.search.return_value = [doc_chunk]
    mock_engine.summarize.return_value = "StudyPilot AI Engine overview summary."
    mock_engine.generate_notes.return_value = "- Key bullet point note."
    mock_engine.generate_quiz.return_value = [
        QuizQuestion(
            question="What is StudyPilot?",
            options=["AI Platform", "Calculator", "Search Engine", "Game"],
            correct_answer_index=0,
            explanation="StudyPilot is an AI study platform.",
        )
    ]
    set_ai_engine(mock_engine)

    try:
        headers_a = _get_auth_header("user_a")
        headers_b = _get_auth_header("user_b")

        # 1. Ingest resource for User A
        pdf_bytes = b"%PDF-1.4 sample content"
        files = {"file": ("doc_a.pdf", pdf_bytes, "application/pdf")}
        res_ingest = client.post("/api/resources/pdf", files=files, headers=headers_a)
        assert res_ingest.status_code == 201
        res_id = res_ingest.json()["resource_id"]

        # 2. Chat (User A) -> 200 OK
        res_chat = client.post(
            "/api/chat",
            json={"message": "What is StudyPilot?", "resource_id": res_id},
            headers=headers_a,
        )
        assert res_chat.status_code == 200
        chat_data = res_chat.json()
        assert "StudyPilot" in chat_data["answer"]

        # 3. Cross-user Chat attempt (User B) -> 404 Not Found
        res_chat_cross = client.post(
            "/api/chat",
            json={"message": "What is StudyPilot?", "resource_id": res_id},
            headers=headers_b,
        )
        assert res_chat_cross.status_code == 404

        # 4. Search (User A) -> 200 OK
        res_search = client.post(
            f"/api/resources/{res_id}/search",
            json={"query": "RAG architecture", "top_k": 3},
            headers=headers_a,
        )
        assert res_search.status_code == 200

        # 5. Summary (User A) -> 200 OK
        res_sum1 = client.post(
            f"/api/resources/{res_id}/summary",
            json={"force_regenerate": False},
            headers=headers_a,
        )
        assert res_sum1.status_code == 200
        sum1_data = res_sum1.json()
        assert "summary" in sum1_data
        assert sum1_data["cached"] is False

        # 6. Summary 2nd call (User A) -> 200 OK (DB cached)
        res_sum2 = client.get(f"/api/resources/{res_id}/summary", headers=headers_a)
        assert res_sum2.status_code == 200
        assert res_sum2.json()["cached"] is True

        # 7. Cross-user Summary attempt (User B) -> 404 Not Found
        res_sum_cross = client.get(f"/api/resources/{res_id}/summary", headers=headers_b)
        assert res_sum_cross.status_code == 404

        # 8. Notes Generation (User A) -> 200 OK
        res_notes = client.post(
            f"/api/resources/{res_id}/notes",
            json={"style": "bullet"},
            headers=headers_a,
        )
        assert res_notes.status_code == 200
        assert "bullet" in res_notes.json()["content"]

        # 9. Quiz Generation (User A) -> 200 OK
        res_quiz = client.post(
            f"/api/resources/{res_id}/quiz",
            json={"question_count": 1, "difficulty": "medium"},
            headers=headers_a,
        )
        assert res_quiz.status_code == 200
        quiz_data = res_quiz.json()
        assert len(quiz_data["questions"]) == 1
        assert quiz_data["questions"][0]["question"] == "What is StudyPilot?"

        # 10. Cross-user DELETE attempt (User B) -> 404 Not Found (Unauthorized deletion blocked)
        res_del_cross = client.delete(f"/api/resources/{res_id}/summary", headers=headers_b)
        assert res_del_cross.status_code == 404

        # 11. Delete Summary (User A) -> 200 OK
        res_del_sum = client.delete(f"/api/resources/{res_id}/summary", headers=headers_a)
        assert res_del_sum.status_code == 200

        # 12. Delete Notes (User A) -> 200 OK
        res_del_notes = client.delete(f"/api/resources/{res_id}/notes", headers=headers_a)
        assert res_del_notes.status_code == 200

        # 13. Delete Quizzes (User A) -> 200 OK
        res_del_quiz = client.delete(f"/api/resources/{res_id}/quizzes", headers=headers_a)
        assert res_del_quiz.status_code == 200

    finally:
        reset_ai_engine()
