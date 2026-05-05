import uuid
import asyncpg
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from agentia.config import DATABASE_URL, PSYCOPG_DATABASE_URL
from agentia.health import get_health
from agentia.logging import setup_logging
from agentia.memory import get_redis, load_context, save_context, persist_messages
from agentia import graph as graph_module
from langchain_core.messages import HumanMessage

setup_logging()
log = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 啟動時：建立資料庫連線池與 Checkpointer
    # 注意：必須設定 autocommit=True 以允許 checkpointer 執行 CREATE INDEX CONCURRENTLY
    async with AsyncConnectionPool(
        conninfo=PSYCOPG_DATABASE_URL, 
        max_size=20,
        kwargs={"autocommit": True}
    ) as pool:
        checkpointer = AsyncPostgresSaver(pool)
        # 建立必要的工作資料表
        await checkpointer.setup()
        
        # 注入具備持久化能力的 Graph
        graph_module.graph = graph_module.build_graph(checkpointer=checkpointer)
        
        log.info("app.startup", checkpointer="AsyncPostgresSaver")
        yield
    # 關閉時：Pool 會自動關閉
    log.info("app.shutdown")

app = FastAPI(title="Agentia", lifespan=lifespan)


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

    logger = log.bind(thread_id=thread_id)

    try:
        while True:
            user_text = await websocket.receive_text()
            logger.info("turn.start", user_text=user_text[:80])

            # 在 M2 Checkpointer 模式下：
            # 1. 我們不再手動載入 history。
            # 2. 我們只需要發送當前的 HumanMessage。
            # 3. LangGraph 會根據 thread_id 自動從 Postgres 載入先前的狀態。
            
            # 設定 Graph 執行參數
            config = {"configurable": {"thread_id": thread_id}}
            # 確保 thread_id 也在 state 中，以便節點記錄日誌
            input_data = {
                "messages": [HumanMessage(content=user_text)],
                "thread_id": thread_id
            }

            ai_chunks: list[str] = []
            async for event in graph_module.graph.astream_events(
                input_data,
                config=config,
                version="v2",
            ):
                if event["event"] == "on_chat_model_stream":
                    token = event["data"]["chunk"].content
                    if token:
                        ai_chunks.append(token)
                        await websocket.send_json({"type": "token", "content": token})

            ai_text = "".join(ai_chunks)
            # 我們仍然保留 persist_messages 用於供歷史紀錄 API (Task 6.5) 查詢
            await persist_messages(thread_id, user_text, ai_text, DATABASE_URL)
            await websocket.send_json({"type": "turn_end"})
            logger.info("turn.end")

    except WebSocketDisconnect:
        logger.info("ws.disconnect")
    finally:
        pass


import os as _os
if _os.path.isdir("frontend"):
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
