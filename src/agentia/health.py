import httpx
import asyncpg
import redis.asyncio as aioredis
import structlog

from agentia.config import DATABASE_URL, LLM_BASE_URL, REDIS_URL

log = structlog.get_logger()


async def check_redis(redis: aioredis.Redis = None) -> bool:
    try:
        if redis is None:
            redis = aioredis.from_url(REDIS_URL)
            should_close = True
        else:
            should_close = False
            
        await redis.ping()
        
        if should_close:
            await redis.aclose()
        return True
    except Exception as exc:
        log.warning("health.redis.failed", error=str(exc))
        return False


async def check_postgres(pool = None) -> bool:
    try:
        if pool is None:
            conn = await asyncpg.connect(dsn=DATABASE_URL.replace("+asyncpg", ""))
            await conn.fetchval("SELECT 1")
            await conn.close()
        else:
            async with pool.connection() as conn:
                await conn.execute("SELECT 1")
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


async def get_health(redis: aioredis.Redis = None, pool = None) -> dict:
    redis_ok, pg_ok, ollama_ok = (
        await check_redis(redis),
        await check_postgres(pool),
        await check_ollama(),
    )
    return {
        "redis": "ok" if redis_ok else "error",
        "postgres": "ok" if pg_ok else "error",
        "ollama": "ok" if ollama_ok else "error",
    }
