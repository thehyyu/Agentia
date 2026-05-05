import json
import asyncpg
import redis.asyncio as aioredis
import structlog
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

from agentia.config import REDIS_URL, DATABASE_URL

log = structlog.get_logger()

CONTEXT_WINDOW = 10
SESSION_TTL = 3600


async def get_redis() -> aioredis.Redis:
    return aioredis.from_url(REDIS_URL, decode_responses=True)


async def load_context(thread_id: str, redis: aioredis.Redis) -> list[BaseMessage]:
    raw = await redis.lrange(f"session:{thread_id}", 0, CONTEXT_WINDOW - 1)
    if len(raw) == CONTEXT_WINDOW:
        log.warning("context.truncated", thread_id=thread_id, kept=CONTEXT_WINDOW)
    messages: list[BaseMessage] = []
    for item in raw:
        data = json.loads(item)
        if data["role"] == "human":
            messages.append(HumanMessage(content=data["content"]))
        else:
            messages.append(AIMessage(content=data["content"]))
    return messages


async def save_context(
    thread_id: str, user_text: str, ai_text: str, redis: aioredis.Redis
) -> None:
    key = f"session:{thread_id}"
    pipe = redis.pipeline()
    pipe.rpush(key, json.dumps({"role": "human", "content": user_text}))
    pipe.rpush(key, json.dumps({"role": "assistant", "content": ai_text}))
    pipe.expire(key, SESSION_TTL)
    await pipe.execute()


async def persist_messages(
    thread_id: str, user_text: str, ai_text: str, db_url: str
) -> None:
    conn = await asyncpg.connect(dsn=db_url.replace("+asyncpg", ""))
    try:
        await conn.executemany(
            "INSERT INTO messages (thread_id, role, content) VALUES ($1, $2, $3)",
            [(thread_id, "user", user_text), (thread_id, "assistant", ai_text)],
        )
    finally:
        await conn.close()
