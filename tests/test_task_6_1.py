import pytest
from fastapi.testclient import TestClient
from agentia.main import app

def test_task_6_1_websocket_connection():
    """
    Task 6.1 TDD: 驗證 WebSocket endpoint 是否能正確建立連線。
    學習點：使用 TestClient.websocket_connect 可以模擬瀏覽器的連線行為。
    """
    client = TestClient(app)
    
    # 嘗試連線到 /ws/chat
    # 我們先不傳入 thread_id，測試其基礎連線能力
    with client.websocket_connect("/ws/chat") as websocket:
        # 如果能進入這個 context，代表連線成功 (HTTP 101 Switching Protocols)
        assert websocket is not None
        
        # 根據草稿實作，連線後應該會收到一個 session_init 訊息
        data = websocket.receive_json()
        assert data["type"] == "session_init"
        assert "thread_id" in data
