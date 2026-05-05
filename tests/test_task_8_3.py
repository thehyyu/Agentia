import pytest
from fastapi.testclient import TestClient
from agentia.main import app
import anyio

def test_task_8_3_memory_is_working_with_checkpointer():
    """
    Task 8.3 TDD (GREEN): 驗證在移除 Redis 後，使用 LangGraph Checkpointer 系統能正確記住對話。
    """
    async def run_test():
        async with app.router.lifespan_context(app):
            with TestClient(app) as client:
                with client.websocket_connect("/ws/chat") as websocket:
                    websocket.receive_json() # session_init
                    
                    # 1. 告訴 AI 名字
                    websocket.send_text("你好，我叫小明。")
                    while True:
                        if websocket.receive_json()["type"] == "turn_end": break
                    
                    # 2. 詢問名字
                    websocket.send_text("我剛才說我叫什麼名字？")
                    tokens = []
                    while True:
                        data = websocket.receive_json()
                        if data["type"] == "token":
                            tokens.append(data["content"])
                        if data["type"] == "turn_end": break
                    
                    full_response = "".join(tokens)
                    print(f"\nAI 的回應 (預期記得): {full_response}")
                    
                    # 斷言：AI 應該記得小明
                    assert "小明" in full_response

    anyio.run(run_test)
