import json
import pytest
import redis.asyncio as aioredis
from agentia.memory import save_context, get_redis

@pytest.mark.asyncio
async def test_save_context_writes_to_redis_with_ttl():
    """
    Task 4.2 TDD: Verify save_context correctly writes user and assistant messages
    to Redis and sets the TTL to 3600 seconds.
    """
    redis = await get_redis()
    thread_id = "test_thread_42"
    user_text = "hello"
    ai_text = "hi there"
    key = f"session:{thread_id}"

    # Cleanup before test
    await redis.delete(key)

    try:
        # Act
        await save_context(thread_id, user_text, ai_text, redis)

        # Assert: Check messages in Redis
        messages = await redis.lrange(key, 0, -1)
        assert len(messages) == 2
        
        m1 = json.loads(messages[0])
        assert m1["role"] == "human"
        assert m1["content"] == user_text
        
        m2 = json.loads(messages[1])
        assert m2["role"] == "assistant"
        assert m2["content"] == ai_text

        # Assert: Check TTL
        ttl = await redis.ttl(key)
        assert 3500 <= ttl <= 3600

    finally:
        # Cleanup
        await redis.delete(key)
        await redis.aclose()
