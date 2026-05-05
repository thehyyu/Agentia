import json
import pytest
from structlog.testing import capture_logs
from agentia.memory import load_context, get_redis, CONTEXT_WINDOW

@pytest.mark.asyncio
async def test_load_context_warns_on_truncation():
    """
    Task 4.4 TDD: Verify that load_context logs a warning when context window is full.
    """
    redis = await get_redis()
    thread_id = "test_thread_44"
    key = f"session:{thread_id}"
    
    # Setup: Fill Redis with exactly CONTEXT_WINDOW (10) messages
    await redis.delete(key)
    for i in range(CONTEXT_WINDOW):
        await redis.rpush(key, json.dumps({"role": "human", "content": f"msg {i}"}))

    try:
        # Act: Capture logs while loading context
        with capture_logs() as logs:
            messages = await load_context(thread_id, redis)
        
        # Assert: Check messages count
        assert len(messages) == CONTEXT_WINDOW
        
        # Assert: Check for the specific warning event
        # structlog.testing.capture_logs returns a list of dicts
        warn_log = next((l for l in logs if l.get("log_level") == "warning" and l.get("event") == "context.truncated"), None)
        assert warn_log is not None, f"Expected context.truncated warning log, but found: {logs}"
        assert warn_log["thread_id"] == thread_id
        assert warn_log["kept"] == CONTEXT_WINDOW

    finally:
        await redis.delete(key)
        await redis.aclose()
