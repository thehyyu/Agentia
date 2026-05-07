"""Task 15.3: get_conversation endpoint uses injected DB pool."""
import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi import FastAPI
from fastapi.testclient import TestClient

from agentia.main import app
from agentia.dependencies import get_db_pool

def test_get_conversation_uses_injected_pool():
    # Mock the pool and its connection/execute flow
    mock_pool = MagicMock()
    mock_conn = AsyncMock()
    mock_pool.connection.return_value.__aenter__.return_value = mock_conn
    
    mock_result = MagicMock()
    mock_result.fetchall = AsyncMock(return_value=[
        ("user", "hello", "2026-05-06 12:00:00")
    ])
    mock_conn.execute.return_value = mock_result

    # Override the dependency
    app.dependency_overrides[get_db_pool] = lambda: mock_pool
    
    try:
        client = TestClient(app)
        response = client.get("/api/conversations/test-thread")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["role"] == "user"
        assert data[0]["content"] == "hello"
        
        # Verify the mock was called correctly (using psycopg style if refactored)
        mock_conn.execute.assert_called_once()
    finally:
        app.dependency_overrides.clear()
