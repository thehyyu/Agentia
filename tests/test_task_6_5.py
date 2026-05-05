import pytest
import asyncpg
import uuid
from fastapi.testclient import TestClient
from agentia.main import app
from agentia.config import DATABASE_URL

@pytest.mark.integration
def test_task_6_5_get_conversation_history():
    """
    Task 6.5 TDD (RED): 驗證歷史紀錄 API 是否能正確回傳資料庫中的訊息。
    """
    client = TestClient(app)
    thread_id = f"test-history-{uuid.uuid4().hex[:6]}"
    db_url = DATABASE_URL.replace("+asyncpg", "")
    
    # 1. 預先塞入測試資料
    # 注意：我們直接在測試中下 SQL，這是為了保證環境受控
    import asyncio
    async def seed_data():
        conn = await asyncpg.connect(dsn=db_url)
        try:
            await conn.executemany(
                "INSERT INTO messages (thread_id, role, content) VALUES ($1, $2, $3)",
                [
                    (thread_id, "user", "Hello first"),
                    (thread_id, "assistant", "Hi first response")
                ]
            )
        finally:
            await conn.close()
            
    # 在 pytest-asyncio 環境下執行這個小 helper
    asyncio.run(seed_data())

    try:
        # 2. 呼叫 API
        response = client.get(f"/api/conversations/{thread_id}")
        
        # 3. 斷言 (Expected RED: 這裡應該會失敗，目前是 404)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["role"] == "user"
        assert data[0]["content"] == "Hello first"
        assert data[1]["role"] == "assistant"
        assert data[1]["content"] == "Hi first response"
        
    finally:
        # 4. 清理測試資料
        async def cleanup():
            conn = await asyncpg.connect(dsn=db_url)
            await conn.execute("DELETE FROM messages WHERE thread_id = $1", thread_id)
            await conn.close()
        asyncio.run(cleanup())
