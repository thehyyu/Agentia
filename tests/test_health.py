import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from agentia.dependencies import get_db_pool, get_redis


@pytest.fixture()
def client():
    from agentia.main import app
    # Override dependencies that require app.state
    app.dependency_overrides[get_db_pool] = lambda: MagicMock()
    app.dependency_overrides[get_redis] = lambda: AsyncMock()
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_health_returns_200_when_all_ok(client):
    all_ok = {"redis": True, "postgres": True, "ollama": True}
    with patch("agentia.main.get_health", new_callable=AsyncMock) as mock:
        mock.return_value = {"redis": "ok", "postgres": "ok", "ollama": "ok"}
        resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_health_returns_503_when_any_degraded(client):
    with patch("agentia.main.get_health", new_callable=AsyncMock) as mock:
        mock.return_value = {"redis": "ok", "postgres": "error", "ollama": "ok"}
        resp = client.get("/health")
    assert resp.status_code == 503
    assert resp.json()["status"] == "degraded"


def test_health_response_contains_checks(client):
    checks = {"redis": "ok", "postgres": "ok", "ollama": "ok"}
    with patch("agentia.main.get_health", new_callable=AsyncMock) as mock:
        mock.return_value = checks
        resp = client.get("/health")
    assert resp.json()["checks"] == checks
