"""Task 14.4: confirmation timeout behaviour."""
import asyncio
import pytest
from agentia.hitl import wait_for_confirmation

TIMEOUT_SECS = 60


@pytest.mark.asyncio
async def test_wait_for_confirmation_returns_true_on_approval():
    async def approved_receive():
        return '{"type": "confirmation_response", "approved": true}'

    result = await wait_for_confirmation(approved_receive, timeout=5)
    assert result is True


@pytest.mark.asyncio
async def test_wait_for_confirmation_returns_false_on_rejection():
    async def rejected_receive():
        return '{"type": "confirmation_response", "approved": false}'

    result = await wait_for_confirmation(rejected_receive, timeout=5)
    assert result is False


@pytest.mark.asyncio
async def test_wait_for_confirmation_returns_timeout_string_on_timeout():
    async def slow_receive():
        await asyncio.sleep(10)
        return '{"type": "confirmation_response", "approved": true}'

    result = await wait_for_confirmation(slow_receive, timeout=0.05)
    assert result == "timeout"
