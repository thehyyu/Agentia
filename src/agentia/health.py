import httpx
import asyncpg
import redis.asyncio as aioredis
import structlog

from agentia.config import DATABASE_URL, LLM_BASE_URL, REDIS_URL

log = structlog.get_logger()


async def check_redis() -> bool:
    try:
        r = aioredis.from_url(REDIS_URL)
        await r.ping()
        await r.aclose()
        return True
    except Exception as exc:
        log.warning("health.redis.failed", error=str(exc))
        return False


async def check_postgres() -> bool:
    try:
        conn = await asyncpg.connect(dsn=DATABASE_URL.replace("+asyncpg", ""))
        await conn.fetchval("SELECT 1")
        await conn.close()
        return True
    except Exception as exc:
        log.warning("health.postgres.failed", error=str(exc))
        return False


async def check_ollama() -> bool:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{LLM_BASE_URL}/api/tags")
            return resp.status_code == 200
    except Exception as exc:
        log.warning("health.ollama.failed", error=str(exc))
        return False


async def get_health() -> dict:
    redis_ok, pg_ok, ollama_ok = (
        await check_redis(),
        await check_postgres(),
        await check_ollama(),
    )
    return {
        "redis": "ok" if redis_ok else "error",
        "postgres": "ok" if pg_ok else "error",
        "ollama": "ok" if ollama_ok else "error",
    }
