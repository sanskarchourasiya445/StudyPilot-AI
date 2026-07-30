from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from ai_engine.engine import EngineHealth
from backend.app.ai.engine_provider import set_ai_engine, reset_ai_engine
from backend.app.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    mock_engine = MagicMock()
    mock_engine.health.return_value = EngineHealth(
        initialized=True,
        vector_store_reachable=True,
        embedding_model_loaded=True,
        llm_configured=True,
    )
    mock_engine.version.return_value = "1.1.0"
    set_ai_engine(mock_engine)

    try:
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert data["backend"] == "online"
        assert data["database"] == "connected"
        assert data["ai_engine"]["initialized"] is True
        assert data["ai_engine"]["vector_store_reachable"] is True
        assert data["ai_engine"]["embedding_model_loaded"] is True
        assert data["ai_engine"]["llm_configured"] is True
        assert data["version"] == "1.0.0"
        assert data["engine_version"] == "1.1.0"
    finally:
        reset_ai_engine()


def test_root_redirect() -> None:
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["docs"] == "/docs"
    assert data["health"] == "/api/health"
