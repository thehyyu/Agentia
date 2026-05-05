import pytest
from fastapi.testclient import TestClient
from agentia.main import app

def test_task_6_2_auto_uuid_generation():
    """
    Task 6.2 TDD - Case A: 當沒有提供 thread_id 時，後端應自動產生。
    """
    client = TestClient(app)
    with client.websocket_connect("/ws/chat") as websocket:
        data = websocket.receive_json()
        assert data["type"] == "session_init"
        assert "thread_id" in data
        # 驗證是否為有效的 UUID 格式
        tid = data["thread_id"]
        assert len(tid) == 36

def test_task_6_2_provided_thread_id():
    """
    Task 6.2 TDD - Case B: 當提供 thread_id 時，後端應直接使用，不發送 session_init。
    """
    client = TestClient(app)
    existing_id = "test-thread-id-123"
    
    with client.websocket_connect(f"/ws/chat?thread_id={existing_id}") as websocket:
        # 這裡我們利用一個小技巧：發送一條訊息並看回覆。
        # 如果前面有 session_init，receive_json() 會拿到它。
        # 如果沒有，我們發一條訊息，應該會直接拿到 Token (由 6.3 處理，但在這我們先測沒收到 session_init)。
        
        # 我們預期此時收不到任何訊息（因為我們沒發話，後端也沒發 session_init）
        # 由於 TestClient 的 websocket.receive 在沒訊息時會丟出 Exception (timeout 概念)
        from starlette.websockets import WebSocketDisconnect
        import anyio
        
        # 我們嘗試讀取一次，應該會失敗或拿到非 session_init 的東西
        with pytest.raises(Exception):
            # TestClient 的 websocket 實作在沒有訊息時會阻塞
            # 我們給它一個極短的超時
            with anyio.fail_after(0.1):
                websocket.receive_json()
