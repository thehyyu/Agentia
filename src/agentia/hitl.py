import asyncio
import json
from typing import Any, Callable, Coroutine


def extract_pending_interrupt(state: Any) -> dict | None:
    """Return the interrupt payload if the graph is paused, else None."""
    if not state.next:
        return None
    for task in state.tasks:
        for intr in task.interrupts:
            return intr.value
    return None


async def wait_for_confirmation(
    receive_fn: Callable[[], Coroutine],
    timeout: float = 60,
) -> bool | str:
    """Wait for a confirmation_response WebSocket message.

    Returns True (approved), False (rejected), or "timeout" if the wait expires.
    receive_fn is an async callable that returns the raw WebSocket text.
    """
    try:
        raw = await asyncio.wait_for(receive_fn(), timeout=timeout)
        msg = parse_ws_message(raw)
        if msg.get("type") == "confirmation_response":
            return bool(msg.get("approved", False))
        return False
    except asyncio.TimeoutError:
        return "timeout"


def parse_ws_message(raw: str) -> dict:
    """Parse an incoming WebSocket message into a typed dict.

    Plain text → {"type": "chat", "content": raw}
    JSON with type field → returned as-is
    """
    try:
        data = json.loads(raw)
        if isinstance(data, dict) and "type" in data:
            return data
    except (json.JSONDecodeError, ValueError):
        pass
    return {"type": "chat", "content": raw}
