"""Task 15.2: WebSocket endpoint uses DI; global graph_module.graph is removed."""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from agentia.main import app
from agentia.dependencies import get_graph


def test_dependency_override_reaches_websocket_handler():
    """Verify DI wiring: overriding get_graph changes what the endpoint sees."""
    fake_graph = MagicMock()
    # astream_events must be an async generator
    async def _no_events(*a, **kw):
        return
        yield  # make it an async generator

    fake_graph.astream_events = _no_events
    fake_graph.checkpointer = None

    captured = {}

    original_get_graph = get_graph

    def override_get_graph():
        captured["graph"] = fake_graph
        return fake_graph

    app.dependency_overrides[get_graph] = override_get_graph
    try:
        client = TestClient(app)
        with client.websocket_connect("/ws/chat") as ws:
            ws.receive_json()  # session_init
            ws.send_text("hello")
            while True:
                data = ws.receive_json()
                if data["type"] == "turn_end":
                    break
    except Exception:
        pass
    finally:
        app.dependency_overrides.clear()

    assert "graph" in captured, "get_graph dependency was not called"
    assert captured["graph"] is fake_graph
