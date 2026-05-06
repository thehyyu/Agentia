"""Tests for Task 14.2 and 14.3: interrupt detection and WebSocket resume flow."""
import json
import pytest
from agentia.hitl import extract_pending_interrupt, parse_ws_message


def test_extract_pending_interrupt_returns_none_when_no_interrupt():
    """Normal completed state has no pending interrupt."""

    class FakeTask:
        interrupts = []

    class FakeState:
        next = []
        tasks = [FakeTask()]

    assert extract_pending_interrupt(FakeState()) is None


def test_extract_pending_interrupt_returns_payload_when_paused():
    """Paused graph state should yield the interrupt payload."""

    class FakeInterrupt:
        value = {"tool": "get_current_datetime", "args": {}}

    class FakeTask:
        interrupts = [FakeInterrupt()]

    class FakeState:
        next = ["confirm_tool"]
        tasks = [FakeTask()]

    result = extract_pending_interrupt(FakeState())
    assert result == {"tool": "get_current_datetime", "args": {}}


def test_parse_ws_message_plain_text_is_chat():
    msg = parse_ws_message("你好")
    assert msg["type"] == "chat"
    assert msg["content"] == "你好"


def test_parse_ws_message_json_chat():
    raw = json.dumps({"type": "chat", "content": "hello"})
    msg = parse_ws_message(raw)
    assert msg["type"] == "chat"
    assert msg["content"] == "hello"


def test_parse_ws_message_confirmation_response_approved():
    raw = json.dumps({"type": "confirmation_response", "approved": True})
    msg = parse_ws_message(raw)
    assert msg["type"] == "confirmation_response"
    assert msg["approved"] is True


def test_parse_ws_message_confirmation_response_rejected():
    raw = json.dumps({"type": "confirmation_response", "approved": False})
    msg = parse_ws_message(raw)
    assert msg["type"] == "confirmation_response"
    assert msg["approved"] is False
