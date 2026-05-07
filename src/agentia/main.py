import uuid
import asyncpg
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.types import Command

from fastapi import Depends

from agentia.config import DATABASE_URL, PSYCOPG_DATABASE_URL
from agentia.health import get_health
from agentia.logging import setup_logging
from agentia.memory import get_redis, load_context, save_context, persist_messages
from agentia import graph as graph_module
from agentia.tools import ALL_TOOLS
from agentia.events import process_graph_event
from agentia.observability import make_langfuse_handler
from agentia.hitl import extract_pending_interrupt, parse_ws_message, wait_for_confirmation
from agentia.dependencies import get_graph, get_db_pool, get_redis
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
        app.state.pool = pool
        checkpointer = AsyncPostgresSaver(pool)
        # 建立必要的工作資料表
        await checkpointer.setup()
        
        # 注入具備持久化能力的 Graph，存入 app.state 供 DI 使用
        app.state.graph = graph_module.build_graph(checkpointer=checkpointer, tools=ALL_TOOLS)
        
        log.info("app.startup", checkpointer="AsyncPostgresSaver")
        yield
    # 關閉時：Pool 會自動關閉
    log.info("app.shutdown")

app = FastAPI(title="Agentia", lifespan=lifespan)


@app.get("/health")
async def health(pool=Depends(get_db_pool), redis=Depends(get_redis)):
    status = await get_health(redis=redis, pool=pool)
    all_ok = all(v == "ok" for v in status.values())
    return JSONResponse(
        content={"status": "ok" if all_ok else "degraded", "checks": status},
        status_code=200 if all_ok else 503,
    )


@app.get("/api/conversations/{thread_id}")
async def get_conversation(thread_id: str, pool=Depends(get_db_pool)):
    async with pool.connection() as conn:
        rows = await conn.execute(
            "SELECT role, content, created_at FROM messages "
            "WHERE thread_id = %s ORDER BY created_at ASC",
            (thread_id,),
        )
        return [
            {"role": r[0], "content": r[1], "created_at": str(r[2])}
            for r in await rows.fetchall()
        ]


@app.websocket("/ws/chat")
async def chat_ws(websocket: WebSocket, thread_id: str = "", graph=Depends(get_graph)):
    await websocket.accept()
    if not thread_id:
        thread_id = str(uuid.uuid4())
        await websocket.send_json({"type": "session_init", "thread_id": thread_id})

    logger = log.bind(thread_id=thread_id)

    callbacks = [h for h in [make_langfuse_handler()] if h is not None]
    config = {
        "configurable": {"thread_id": thread_id},
        "callbacks": callbacks,
        "metadata": {
            "langfuse_session_id": thread_id,
            "langfuse_trace_name": "chat-response",
        },
    }

    try:
        while True:
            raw = await websocket.receive_text()
            incoming = parse_ws_message(raw)

            if incoming["type"] == "confirmation_response":
                # Should not arrive here outside of the HITL flow; ignore silently.
                continue

            user_text = incoming.get("content", raw)
            logger.info("turn.start", user_text=user_text[:80])

            graph_input = {
                "messages": [HumanMessage(content=user_text)],
                "thread_id": thread_id,
            }

            ai_chunks: list[str] = []

            async def _stream(graph_in):
                async for event in graph.astream_events(
                    graph_in, config=config, version="v2"
                ):
                    msg = process_graph_event(event)
                    if msg is not None:
                        if msg["type"] == "token":
                            ai_chunks.append(msg["content"])
                        await websocket.send_json(msg)

            await _stream(graph_input)

            # HITL: check for pending interrupt after each stream run
            # (requires checkpointer — skipped in tests that run without lifespan)
            while graph.checkpointer is not None:
                state = await graph.aget_state(config)
                interrupt_payload = extract_pending_interrupt(state)
                if interrupt_payload is None:
                    break

                await websocket.send_json({
                    "type": "confirmation_request",
                    **interrupt_payload,
                })
                logger.info("hitl.interrupt", tool=interrupt_payload.get("tool"))

                approved = await wait_for_confirmation(
                    websocket.receive_text, timeout=60
                )
                logger.info("hitl.resume", approved=approved)
                await _stream(Command(resume=approved))

            ai_text = "".join(ai_chunks)
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
