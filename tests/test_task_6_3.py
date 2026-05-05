import pytest
from fastapi.testclient import TestClient
from agentia.main import app

@pytest.mark.integration
def test_task_6_3_token_streaming():
    """
    Task 6.3 TDD: 驗證 WebSocket 是否能逐字 (token) 回傳 AI 的回應。
    學習點：模擬使用者發送訊息，並檢查是否收到連續的 "token" 類型訊息。
    """
    client = TestClient(app)
    with client.websocket_connect("/ws/chat") as websocket:
        # 1. 略過第一條 session_init
        websocket.receive_json()
        
        # 2. 發送使用者訊息
        user_prompt = "請說『你好』這兩個字就好。"
        websocket.send_text(user_prompt)
        
        # 3. 預期會收到多個 token 訊息
        tokens = []
        # 我們嘗試接收幾次，直到拿到特定的結束信號或達到合理次數
        # 在 M1 實作中，我們預期會收到 {"type": "token", "content": "..."}
        for _ in range(50): # 避免無限迴圈
            try:
                data = websocket.receive_json()
                if data["type"] == "token":
                    tokens.append(data["content"])
                elif data["type"] == "turn_end":
                    break
            except Exception:
                break
        
        # 驗證是否真的收到了 token
        assert len(tokens) > 0, "沒有收到任何 token 訊息"
        full_response = "".join(tokens)
        assert "你好" in full_response
        print(f"\n串流收到的完整回應: {full_response}")
        print(f"總共收到 {len(tokens)} 個 token 訊息")
