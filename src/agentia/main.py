import uuid
import asyncpg
import structlog
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from agentia.config import DATABASE_URL
from agentia.health import get_health
from agentia.logging import setup_logging
from agentia.memory import get_redis, load_context, save_context, persist_messages
from agentia.graph import graph
from langchain_core.messages import HumanMessage

setup_logging()
log = structlog.get_logger()

app = FastAPI(title="Agentia")


@app.get("/health")
async def health():
    status = await get_health()
    all_ok = all(v == "ok" for v in status.values())
    return JSONResponse(
        content={"status": "ok" if all_ok else "degraded", "checks": status},
        status_code=200 if all_ok else 503,
    )


@app.get("/api/conversations/{thread_id}")
async def get_conversation(thread_id: str):
    conn = await asyncpg.connect(dsn=DATABASE_URL.replace("+asyncpg", ""))
    try:
        rows = await conn.fetch(
            "SELECT role, content, created_at FROM messages "
            "WHERE thread_id = $1 ORDER BY created_at ASC",
            thread_id,
        )
        return [
            {"role": r["role"], "content": r["content"], "created_at": str(r["created_at"])}
            for r in rows
        ]
    finally:
        await conn.close()


@app.websocket("/ws/chat")
async def chat_ws(websocket: WebSocket, thread_id: str = ""):
    await websocket.accept()
    if not thread_id:
        thread_id = str(uuid.uuid4())
        await websocket.send_json({"type": "session_init", "thread_id": thread_id})

    redis = await get_redis()
    logger = log.bind(thread_id=thread_id)

    try:
        while True:
            user_text = await websocket.receive_text()
            logger.info("turn.start", user_text=user_text[:80])

            history = await load_context(thread_id, redis)
            history.append(HumanMessage(content=user_text))

            ai_chunks: list[str] = []
            async for event in graph.astream_events(
                {"messages": history, "thread_id": thread_id},
                version="v2",
            ):
                if event["event"] == "on_chat_model_stream":
                    token = event["data"]["chunk"].content
                    if token:
                        ai_chunks.append(token)
                        await websocket.send_json({"type": "token", "content": token})

            ai_text = "".join(ai_chunks)
            await save_context(thread_id, user_text, ai_text, redis)
            await persist_messages(thread_id, user_text, ai_text, DATABASE_URL)
            await websocket.send_json({"type": "turn_end"})
            logger.info("turn.end")

    except WebSocketDisconnect:
        logger.info("ws.disconnect")
    finally:
        await redis.aclose()


import os as _os
if _os.path.isdir("frontend"):
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
