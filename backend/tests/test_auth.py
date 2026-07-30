import uuid
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_auth_full_flow() -> None:
    unique_id = uuid.uuid4().hex[:8]
    test_email = f"student_{unique_id}@example.com"
    test_password = "secure_password_123"
    test_name = "Alice Student"

    # 1. Register User
    reg_response = client.post(
        "/api/auth/register",
        json={"email": test_email, "password": test_password, "name": test_name},
    )
    assert reg_response.status_code == 201
    user_data = reg_response.json()
    assert user_data["email"] == test_email
    assert user_data["name"] == test_name
    assert "id" in user_data
    assert "password_hash" not in user_data

    # 2. Duplicate Registration fails with 400
    dup_response = client.post(
        "/api/auth/register",
        json={"email": test_email, "password": test_password, "name": test_name},
    )
    assert dup_response.status_code == 400
    assert "already exists" in dup_response.json()["detail"]

    # 3. Login with wrong password fails with 401
    bad_login = client.post(
        "/api/auth/login",
        json={"email": test_email, "password": "wrong_password"},
    )
    assert bad_login.status_code == 401

    # 4. Login with valid password succeeds with 200 and token
    login_response = client.post(
        "/api/auth/login",
        json={"email": test_email, "password": test_password},
    )
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    token = token_data["access_token"]

    # 5. Access /api/auth/me without token fails with 401
    unauth_me = client.get("/api/auth/me")
    assert unauth_me.status_code == 401

    # 6. Access /api/auth/me with invalid token fails with 401
    invalid_me = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid.token.value"})
    assert invalid_me.status_code == 401

    # 7. Access /api/auth/me with valid Bearer token succeeds with 200
    me_response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_response.status_code == 200
    me_data = me_response.json()
    assert me_data["id"] == user_data["id"]
    assert me_data["email"] == test_email
    assert me_data["name"] == test_name
