import uuid
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient
from langchain_core.documents import Document
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


def test_conversations_persistence_and_security() -> None:
    mock_engine = MagicMock()
    doc_chunk = Document(page_content="Sample grounding text.", metadata={"source": "lecture.pdf"})
    mock_engine.chat.return_value = ChatResult(
        answer="Grounded answer from AI engine.",
        sources=[doc_chunk],
    )
    mock_engine.ask.return_value = mock_engine.chat.return_value
    set_ai_engine(mock_engine)

    try:
        headers_a = _get_auth_header("user_a")
        headers_b = _get_auth_header("user_b")

        # 1. Create explicit conversation for User A
        res_create = client.post(
            "/api/conversations",
            json={"title": "Physics Revision"},
            headers=headers_a,
        )
        assert res_create.status_code == 201
        conv_a1 = res_create.json()
        conv_id_a1 = conv_a1["id"]
        assert conv_a1["title"] == "Physics Revision"

        # 2. Chat with explicit conversation_id
        res_chat1 = client.post(
            "/api/chat",
            json={"message": "Explain Newton's First Law", "conversation_id": conv_id_a1},
            headers=headers_a,
        )
        assert res_chat1.status_code == 200
        assert res_chat1.json()["conversation_id"] == conv_id_a1

        # 3. Chat without conversation_id -> should auto-create persistent conversation
        res_chat2 = client.post(
            "/api/chat",
            json={"message": "What is Quantum Mechanics?"},
            headers=headers_a,
        )
        assert res_chat2.status_code == 200
        conv_id_auto = res_chat2.json()["conversation_id"]
        assert conv_id_auto is not None
        assert conv_id_auto != conv_id_a1

        # 4. List User A's conversations -> should see 2 conversations
        res_list_a = client.get("/api/conversations", headers=headers_a)
        assert res_list_a.status_code == 200
        convs_a = res_list_a.json()
        assert len(convs_a) == 2

        # 5. Get message history for conversation A1 -> 2 messages (1 user, 1 assistant)
        res_msgs = client.get(f"/api/conversations/{conv_id_a1}/messages", headers=headers_a)
        assert res_msgs.status_code == 200
        msgs = res_msgs.json()
        assert len(msgs) == 2
        assert msgs[0]["role"] == "user"
        assert msgs[0]["content"] == "Explain Newton's First Law"
        assert msgs[1]["role"] == "assistant"
        assert "Grounded answer" in msgs[1]["content"]

        # 6. Cross-user Security Checks (User B accessing User A's conversation)
        assert client.get(f"/api/conversations/{conv_id_a1}", headers=headers_b).status_code == 404
        assert client.get(f"/api/conversations/{conv_id_a1}/messages", headers=headers_b).status_code == 404
        assert client.delete(f"/api/conversations/{conv_id_a1}", headers=headers_b).status_code == 404

        # 7. Delete conversation as User A -> 200 OK
        res_del = client.delete(f"/api/conversations/{conv_id_a1}", headers=headers_a)
        assert res_del.status_code == 200

        # 8. Verify messages and conversation deleted
        assert client.get(f"/api/conversations/{conv_id_a1}", headers=headers_a).status_code == 404
        assert len(client.get("/api/conversations", headers=headers_a).json()) == 1

    finally:
        reset_ai_engine()
