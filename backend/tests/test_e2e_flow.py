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


def test_full_student_journey_e2e() -> None:
    # 0. Setup Mock AI Engine
    unique_res_id = f"res_e2e_{uuid.uuid4().hex[:8]}"
    mock_engine = MagicMock()
    mock_engine.ingest.return_value = IngestionResult(
        source="quantum_physics.pdf",
        source_type="pdf",
        pages_or_segments=12,
        chunks_created=35,
        resource_id=unique_res_id,
    )
    doc_chunk = Document(
        page_content="Quantum entanglement is a phenomenon in quantum mechanics...",
        metadata={"source": "quantum_physics.pdf"},
    )
    mock_engine.ask.return_value = ChatResult(
        answer="Quantum entanglement connects quantum states instantly across distance.",
        sources=[doc_chunk],
    )
    mock_engine.search.return_value = [doc_chunk]
    mock_engine.summarize.return_value = "Comprehensive summary of Quantum Mechanics chapter."
    mock_engine.generate_notes.return_value = "- Superposition\n- Entanglement\n- Wave-particle duality"
    mock_engine.generate_quiz.return_value = [
        QuizQuestion(
            question="What is Quantum Entanglement?",
            options=["Phenomenon", "Chemical reaction", "Gravitational force", "Thermal wave"],
            correct_answer_index=0,
            explanation="Quantum entanglement connects particle states.",
        )
    ]
    mock_engine.delete_resource.return_value = 35
    set_ai_engine(mock_engine)

    try:
        # 1. Register Student A
        email_a = f"student_a_{uuid.uuid4().hex[:8]}@example.com"
        reg_a = client.post(
            "/api/auth/register",
            json={"email": email_a, "password": "secure_pass_123", "name": "Student Alice"},
        )
        assert reg_a.status_code == 201

        # 2. Login Student A
        login_a = client.post(
            "/api/auth/login",
            json={"email": email_a, "password": "secure_pass_123"},
        )
        assert login_a.status_code == 200
        token_a = login_a.json()["access_token"]
        headers_a = {"Authorization": f"Bearer {token_a}"}

        # 3. Get Me Profile
        me_a = client.get("/api/auth/me", headers=headers_a)
        assert me_a.status_code == 200
        assert me_a.json()["email"] == email_a

        # 4. Upload PDF Resource
        pdf_bytes = b"%PDF-1.4 sample Quantum Physics textbook content"
        files = {"file": ("quantum_physics.pdf", pdf_bytes, "application/pdf")}
        res_ingest = client.post("/api/resources/pdf", files=files, headers=headers_a)
        assert res_ingest.status_code == 201
        res_id = res_ingest.json()["resource_id"]
        assert res_id == unique_res_id

        # 5. List Resources
        res_list = client.get("/api/resources", headers=headers_a)
        assert res_list.status_code == 200
        assert len(res_list.json()) == 1
        assert res_list.json()[0]["resource_id"] == res_id

        # 6. Perform Vector Search
        res_search = client.post(
            f"/api/resources/{res_id}/search",
            json={"query": "entanglement", "top_k": 2},
            headers=headers_a,
        )
        assert res_search.status_code == 200
        assert len(res_search.json()["results"]) == 1

        # 7. Initial RAG Chat (auto-creates conversation)
        res_chat1 = client.post(
            "/api/chat",
            json={"message": "What is quantum entanglement?", "resource_id": res_id},
            headers=headers_a,
        )
        assert res_chat1.status_code == 200
        chat1_data = res_chat1.json()
        conv_id = chat1_data["conversation_id"]
        assert conv_id is not None
        assert "Quantum entanglement" in chat1_data["answer"]

        # 8. Follow-up RAG Chat with explicit conversation_id
        res_chat2 = client.post(
            "/api/chat",
            json={"message": "Can you summarize key principles?", "conversation_id": conv_id},
            headers=headers_a,
        )
        assert res_chat2.status_code == 200
        assert res_chat2.json()["conversation_id"] == conv_id

        # 9. Get Conversation Message History
        res_msgs = client.get(f"/api/conversations/{conv_id}/messages", headers=headers_a)
        assert res_msgs.status_code == 200
        msgs = res_msgs.json()
        assert len(msgs) == 4  # (2 user prompts + 2 assistant responses)

        # 10. Generate Summary (Cache Miss)
        res_sum1 = client.post(
            f"/api/resources/{res_id}/summary",
            json={"force_regenerate": False},
            headers=headers_a,
        )
        assert res_sum1.status_code == 200
        assert res_sum1.json()["cached"] is False

        # 11. Re-fetch Summary (Cache Hit)
        res_sum2 = client.get(f"/api/resources/{res_id}/summary", headers=headers_a)
        assert res_sum2.status_code == 200
        assert res_sum2.json()["cached"] is True

        # 12. Generate Study Notes
        res_notes = client.post(
            f"/api/resources/{res_id}/notes",
            json={"style": "bullet"},
            headers=headers_a,
        )
        assert res_notes.status_code == 200
        assert "Superposition" in res_notes.json()["content"]

        # 13. Fetch Existing Notes
        res_get_notes = client.get(f"/api/resources/{res_id}/notes?style=bullet", headers=headers_a)
        assert res_get_notes.status_code == 200

        # 14. Generate Quiz
        res_quiz = client.post(
            f"/api/resources/{res_id}/quiz",
            json={"question_count": 1, "difficulty": "medium"},
            headers=headers_a,
        )
        assert res_quiz.status_code == 200
        assert len(res_quiz.json()["questions"]) == 1

        # 15. List Quizzes
        res_list_quiz = client.get(f"/api/resources/{res_id}/quizzes", headers=headers_a)
        assert res_list_quiz.status_code == 200
        assert len(res_list_quiz.json()) == 1

        # 16. Cross-User Security Check (Student B)
        email_b = f"student_b_{uuid.uuid4().hex[:8]}@example.com"
        reg_b = client.post("/api/auth/register", json={"email": email_b, "password": "secure_pass_456", "name": "Student Bob"})
        assert reg_b.status_code == 201
        login_b = client.post("/api/auth/login", json={"email": email_b, "password": "secure_pass_456"})
        assert login_b.status_code == 200
        token_b = login_b.json()["access_token"]
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # Student B attempting access to Student A's resource / conversation gets 404
        assert client.get(f"/api/resources/{res_id}", headers=headers_b).status_code == 404
        assert client.post(f"/api/resources/{res_id}/search", json={"query": "x"}, headers=headers_b).status_code == 404
        assert client.get(f"/api/resources/{res_id}/summary", headers=headers_b).status_code == 404
        assert client.get(f"/api/conversations/{conv_id}", headers=headers_b).status_code == 404
        assert client.delete(f"/api/resources/{res_id}", headers=headers_b).status_code == 404

        # 17. Cleanup / Delete Resource (Student A)
        res_del = client.delete(f"/api/resources/{res_id}", headers=headers_a)
        assert res_del.status_code == 200
        assert mock_engine.delete_resource.called

    finally:
        reset_ai_engine()
