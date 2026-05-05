import pytest
from fastapi.testclient import TestClient
from agentia.main import app
import anyio

def test_task_8_4_reconnection_persists_state():
    """
    Task 8.4 TDD: 驗證當 WebSocket 斷線後，使用相同 thread_id 重連，對話記憶依然存在。
    學習點：這模擬了前端網頁重新整理或網路不穩後，帶回 thread_id 的真實場景。
    """
    async def run_test():
        async with app.router.lifespan_context(app):
            # 1. 第一次連線：告訴 AI 秘密
            with TestClient(app) as client:
                with client.websocket_connect("/ws/chat") as ws1:
                    data = ws1.receive_json() # session_init
                    original_tid = data["thread_id"]
                    
                    ws1.send_text("我的幸運數字是 777。")
                    while ws1.receive_json()["type"] != "turn_end": pass
                # ws1 連線在此結束 (斷線)

            # 2. 第二次連線：帶回相同的 thread_id
            with TestClient(app) as client:
                with client.websocket_connect(f"/ws/chat?thread_id={original_tid}") as ws2:
                    # 注意：帶了 ID，所以後端不應該再發送 session_init
                    
                    ws2.send_text("我剛才說我的幸運數字是多少？")
                    tokens = []
                    while True:
                        data = ws2.receive_json()
                        if data["type"] == "token":
                            tokens.append(data["content"])
                        if data["type"] == "turn_end": break
                    
                    full_response = "".join(tokens)
                    print(f"\n斷線重連後 AI 的回應: {full_response}")
                    
                    # 斷言：AI 應能從 Postgres Checkpointer 找回之前的對話
                    assert "777" in full_response, "AI 忘了之前的對話，持久化機制失效！"

    anyio.run(run_test)
