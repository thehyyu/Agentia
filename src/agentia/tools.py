from datetime import datetime, timezone

import asyncpg
from langchain_core.tools import tool

from agentia.config import DATABASE_URL


@tool
def get_current_datetime() -> str:
    """回傳目前的日期與時間（ISO 8601 格式）。"""
    return datetime.now(timezone.utc).isoformat()


@tool
async def search_history(query: str) -> str:
    """在對話歷史中搜尋包含關鍵字的訊息，回傳最多 5 筆結果。"""
    conn = await asyncpg.connect(dsn=DATABASE_URL.replace("+asyncpg", ""))
    try:
        rows = await conn.fetch(
            "SELECT role, content FROM messages "
            "WHERE content ILIKE $1 ORDER BY created_at DESC LIMIT 5",
            f"%{query}%",
        )
        if not rows:
            return "未找到相關對話記錄。"
        return "\n".join(f"[{r['role']}] {r['content'][:200]}" for r in rows)
    finally:
        await conn.close()


ALL_TOOLS = [get_current_datetime, search_history]
