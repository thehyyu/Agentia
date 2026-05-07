import json
from datetime import datetime, timezone

import asyncpg
from langchain_core.tools import tool

from agentia.config import DATABASE_URL, LLM_BASE_URL, TAVILY_API_KEY
from agentia.ingest import embed_text


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


@tool
async def retrieve_knowledge(query: str) -> str:
    """在知識庫中搜尋與查詢語意相似的內容，回傳最多 5 個相關片段及相關文章清單。"""
    embedding = await embed_text(query, LLM_BASE_URL)
    conn = await asyncpg.connect(dsn=DATABASE_URL.replace("+asyncpg", ""))
    try:
        rows = await conn.fetch(
            "SELECT doc_id, content FROM chunks ORDER BY embedding <=> $1::vector LIMIT 3",
            str(embedding),
        )
        if not rows:
            return json.dumps({"chunks": "", "related_articles": []}, ensure_ascii=False)

        chunks_text = "\n\n".join(f"[{r['doc_id']}]\n{r['content']}" for r in rows)

        seen: dict[str, bool] = {}
        for r in rows:
            slug = r["doc_id"].rsplit("_", 1)[0]
            seen[slug] = True
        related_articles = list(seen.keys())[:3]

        return json.dumps(
            {"chunks": chunks_text, "related_articles": related_articles},
            ensure_ascii=False,
        )
    finally:
        await conn.close()


@tool
def web_search(query: str) -> str:
    """當知識庫無相關資料時，透過網路搜尋回答問題。回傳原始搜尋結果供 LLM 合成答案。"""
    if not TAVILY_API_KEY:
        return "網路搜尋功能未啟用（未設定 TAVILY_API_KEY）。"
    from tavily import TavilyClient
    client = TavilyClient(api_key=TAVILY_API_KEY)
    results = client.search(query, max_results=5)
    items = results.get("results", [])
    if not items:
        return "未找到相關網路搜尋結果。"
    return json.dumps(
        [{"title": r["title"], "url": r["url"], "content": r.get("content", "")[:500]}
         for r in items],
        ensure_ascii=False,
    )


_base_tools = [get_current_datetime, search_history, retrieve_knowledge]
ALL_TOOLS = _base_tools + ([web_search] if TAVILY_API_KEY else [])
