import pytest
import asyncpg
import uuid
from agentia.memory import persist_messages
from agentia.config import DATABASE_URL

@pytest.mark.asyncio
async def test_persist_messages_inserts_into_db():
    """
    Task 4.3 TDD: Verify persist_messages correctly inserts user and assistant records.
    Behavior: One call should result in two rows in the database.
    """
    thread_id = f"test_thread_{uuid.uuid4().hex[:8]}"
    user_text = "how are you?"
    ai_text = "I am a robot."
    
    # We strip '+asyncpg' because asyncpg uses a standard dsn format for direct connection in test verification
    db_url = DATABASE_URL.replace("+asyncpg", "")

    # Act
    await persist_messages(thread_id, user_text, ai_text, DATABASE_URL)

    # Assert
    conn = await asyncpg.connect(dsn=db_url)
    try:
        rows = await conn.fetch(
            "SELECT role, content FROM messages WHERE thread_id = $1 ORDER BY created_at ASC",
            thread_id
        )
        assert len(rows) == 2
        
        # Verify first row (user)
        assert rows[0]["role"] == "user"
        assert rows[0]["content"] == user_text
        
        # Verify second row (assistant)
        assert rows[1]["role"] == "assistant"
        assert rows[1]["content"] == ai_text
    finally:
        # Cleanup
        await conn.execute("DELETE FROM messages WHERE thread_id = $1", thread_id)
        await conn.close()
