"""Task 15.4: health endpoint uses injected dependencies."""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from agentia.main import app
from agentia.dependencies import get_db_pool, get_redis

def test_health_uses_injected_dependencies():
    # Use MagicMock for the pool so that connection() returns a regular object
    mock_pool = MagicMock()
    mock_conn = AsyncMock()
    
    # The object returned by pool.connection() must be an async context manager
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value = mock_conn
    mock_pool.connection.return_value = mock_ctx
    
    # mock_conn.execute is also an async method in psycopg
    mock_conn.execute = AsyncMock() 

    mock_redis = AsyncMock()
    mock_redis.ping.return_value = True

    # Override the dependencies
    app.dependency_overrides[get_db_pool] = lambda: mock_pool
    app.dependency_overrides[get_redis] = lambda: mock_redis
    
    try:
        # Mocking check_ollama because it still uses httpx internally
        with patch("agentia.health.check_ollama", return_value=True):
            client = TestClient(app)
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert data["checks"]["postgres"] == "ok"
            assert data["checks"]["redis"] == "ok"
            
            # Verify injected mocks were used
            mock_redis.ping.assert_called_once()
            mock_pool.connection.assert_called_once()
    finally:
        app.dependency_overrides.clear()
