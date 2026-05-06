from unittest.mock import MagicMock
from agentia.events import process_graph_event


def _stream_event(content: str) -> dict:
    chunk = MagicMock()
    chunk.content = content
    return {"event": "on_chat_model_stream", "data": {"chunk": chunk}, "name": "ChatOllama"}


def _tool_end_event(tool_name: str, output: str) -> dict:
    return {
        "event": "on_tool_end",
        "name": tool_name,
        "data": {"output": output, "input": {"query": "test"}},
    }


def test_on_chat_model_stream_returns_token_message():
    result = process_graph_event(_stream_event("你好"))
    assert result == {"type": "token", "content": "你好"}


def test_empty_token_returns_none():
    result = process_graph_event(_stream_event(""))
    assert result is None


def test_on_tool_end_returns_none_not_sent_to_websocket():
    result = process_graph_event(_tool_end_event("get_current_datetime", "2026-05-06"))
    assert result is None


def test_unknown_event_returns_none():
    result = process_graph_event({"event": "on_chain_start", "data": {}})
    assert result is None
