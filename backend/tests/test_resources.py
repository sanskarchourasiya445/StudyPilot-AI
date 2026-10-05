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


def test_resource_management_and_ownership() -> None:
    mock_engine = MagicMock()
    unique_pdf_res_id = f"res_mock_{uuid.uuid4().hex[:8]}"
    mock_engine.ingest.return_value = IngestionResult(
        source="test.pdf",
        source_type="pdf",
        pages_or_segments=10,
        chunks_created=25,
        resource_id=unique_pdf_res_id,
    )
    mock_engine.delete_resource.return_value = 25
    set_ai_engine(mock_engine)

    try:
        # Setup User A and User B
        headers_a = _get_auth_header("user_a", "User A")
        headers_b = _get_auth_header("user_b", "User B")

        # 1. User A uploads PDF
        pdf_bytes = b"%PDF-1.4 sample PDF content"
        files = {"file": ("lecture_notes.pdf", pdf_bytes, "application/pdf")}
        res_a1 = client.post("/api/resources/pdf", files=files, headers=headers_a)
        assert res_a1.status_code == 201
        data_a1 = res_a1.json()
        assert data_a1["title"] == "lecture_notes.pdf"
        assert data_a1["source_type"] == "pdf"
        assert data_a1["resource_id"] == unique_pdf_res_id
        res_id_a1 = data_a1["resource_id"]

        # 2. User A ingests YouTube URL
        unique_yt_url = f"https://www.youtube.com/watch?v=test_{uuid.uuid4().hex[:8]}"
        unique_yt_res_id = f"res_yt_{uuid.uuid4().hex[:8]}"
        mock_engine.ingest.return_value = IngestionResult(
            source=unique_yt_url,
            source_type="youtube",
            pages_or_segments=1,
            chunks_created=12,
            resource_id=unique_yt_res_id,
        )
        res_a2 = client.post(
            "/api/resources/youtube",
            json={"url": unique_yt_url, "title": "Rick Roll Lecture"},
            headers=headers_a,
        )
        assert res_a2.status_code == 201
        data_a2 = res_a2.json()
        assert data_a2["title"] == "Rick Roll Lecture"
        assert data_a2["resource_id"] == unique_yt_res_id

        # 3. User A lists resources -> should see 2 resources
        list_a = client.get("/api/resources", headers=headers_a)
        assert list_a.status_code == 200
        items_a = list_a.json()
        assert len(items_a) == 2

        # 4. User B lists resources -> should see 0 resources (User B owns nothing yet)
        list_b = client.get("/api/resources", headers=headers_b)
        assert list_b.status_code == 200
        assert len(list_b.json()) == 0

        # 5. User B tries to access User A's resource -> gets 404 Not Found
        get_cross = client.get(f"/api/resources/{res_id_a1}", headers=headers_b)
        assert get_cross.status_code == 404

        # 6. User B tries to delete User A's resource -> gets 404 Not Found
        del_cross = client.delete(f"/api/resources/{res_id_a1}", headers=headers_b)
        assert del_cross.status_code == 404

        # 7. User A accesses their own resource -> gets 200 OK
        get_own = client.get(f"/api/resources/{res_id_a1}", headers=headers_a)
        assert get_own.status_code == 200
        assert get_own.json()["resource_id"] == res_id_a1

        # 8. User A deletes their resource -> gets 200 OK
        del_own = client.delete(f"/api/resources/{res_id_a1}", headers=headers_a)
        assert del_own.status_code == 200
        mock_engine.delete_resource.assert_called_with(unique_pdf_res_id)

        # 9. Verify User A now has 1 resource left
        list_a_after = client.get("/api/resources", headers=headers_a)
        assert len(list_a_after.json()) == 1

    finally:
        reset_ai_engine()
