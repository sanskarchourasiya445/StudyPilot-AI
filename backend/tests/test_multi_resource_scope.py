import uuid
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient
from langchain_core.documents import Document

from ai_engine.engine import IngestionResult
from ai_engine.services.chat_service import ChatResult
from backend.app.ai.engine_provider import set_ai_engine, reset_ai_engine
from backend.app.main import app

client = TestClient(app)


def _register_user_with_resources(prefix: str, count: int = 2) -> tuple[dict, list[str]]:
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
    headers = {"Authorization": f"Bearer {token}"}

    res_ids = []
    for i in range(count):
        fake_pdf = f"dummy_{i}.pdf".encode("utf-8")
        resp = client.post(
            "/api/resources/pdf",
            files={"file": (f"doc_{i}.pdf", fake_pdf, "application/pdf")},
            headers=headers,
        )
        assert resp.status_code == 201
        res_ids.append(resp.json()["resource_id"])

    return headers, res_ids


def test_multi_resource_scope_chat_and_security() -> None:
    mock_engine = MagicMock()
    mock_engine.ingest.side_effect = lambda source, **kwargs: IngestionResult(
        source=source,
        source_type="pdf",
        pages_or_segments=5,
        chunks_created=10,
        resource_id=f"res_{uuid.uuid4().hex[:8]}",
    )

    doc1 = Document(page_content="Theory detail", metadata={"source": "MongoDB Detailed Theory.pdf", "resource_id": "res-1"})
    doc2 = Document(page_content="Notes detail", metadata={"source": "MongoDB Short Notes.pdf", "resource_id": "res-2"})
    
    mock_engine.chat.return_value = ChatResult(
        answer="Comparing detailed theory and short notes.",
        sources=[doc1, doc2],
    )
    set_ai_engine(mock_engine)

    try:
        headers_a, res_ids_a = _register_user_with_resources("user_a", 3)
        headers_b, res_ids_b = _register_user_with_resources("user_b", 1)

        # 1. Multi-Resource Chat Request
        payload_multi = {
            "message": "Compare theory with short notes",
            "scope": {
                "mode": "selected",
                "resource_ids": [res_ids_a[0], res_ids_a[1]]
            }
        }
        res_multi = client.post("/api/chat", json=payload_multi, headers=headers_a)
        assert res_multi.status_code == 200
        data_multi = res_multi.json()
        
        assert data_multi["scope"]["mode"] == "selected"
        assert set(data_multi["scope"]["resource_ids"]) == set([res_ids_a[0], res_ids_a[1]])
        assert len(data_multi["sources"]) == 2
        conv_id = data_multi["conversation_id"]

        # 2. All-Resources Chat Request
        payload_all = {
            "message": "Overview across my library",
            "scope": {
                "mode": "all",
                "resource_ids": []
            }
        }
        res_all = client.post("/api/chat", json=payload_all, headers=headers_a)
        assert res_all.status_code == 200
        data_all = res_all.json()
        assert data_all["scope"]["mode"] == "all"

        # 3. Conversation Scope Persistence Test
        conv_res = client.get("/api/conversations", headers=headers_a)
        assert conv_res.status_code == 200
        conv_list = conv_res.json()
        target_conv = next(c for c in conv_list if c["id"] == conv_id)
        assert target_conv["scope_mode"] == "selected"
        assert set(target_conv["resource_ids"]) == set([res_ids_a[0], res_ids_a[1]])

        # 4. Security Check: Requesting User B's resource ID under User A's token MUST fail
        payload_sec = {
            "message": "Malicious attempt to read User B resource",
            "scope": {
                "mode": "selected",
                "resource_ids": [res_ids_a[0], res_ids_b[0]]
            }
        }
        res_sec = client.post("/api/chat", json=payload_sec, headers=headers_a)
        assert res_sec.status_code == 404
        assert "not found or not owned by user" in res_sec.json()["detail"]

    finally:
        reset_ai_engine()
