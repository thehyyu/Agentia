"""Task 15.1: FastAPI Depends() provider functions."""
import pytest
from unittest.mock import MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from agentia.dependencies import get_graph


def _app_with_graph(graph_value):
    app = FastAPI()
    app.state.graph = graph_value
    return app


def test_get_graph_returns_app_state_graph():
    fake_graph = MagicMock()
    app = _app_with_graph(fake_graph)

    mock_request = MagicMock()
    mock_request.app = app

    result = get_graph(mock_request)
    assert result is fake_graph


def test_get_graph_raises_when_not_initialized():
    app = FastAPI()  # no graph in app.state

    mock_request = MagicMock()
    mock_request.app = app

    # Mock the fallback module to ensure it also doesn't have a graph
    with patch("agentia.graph.graph", None):
        with pytest.raises(RuntimeError, match="Graph not initialized"):
            get_graph(mock_request)
