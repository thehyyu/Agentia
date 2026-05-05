import pytest
import asyncpg

DB_DSN = "postgresql://agentia:agentia@localhost:5432/agentia"


@pytest.mark.asyncio
async def test_messages_table_exists():
    conn = await asyncpg.connect(dsn=DB_DSN)
    try:
        result = await conn.fetchval(
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_name = 'messages'"
        )
        assert result == 1, "messages table does not exist"
    finally:
        await conn.close()


@pytest.mark.asyncio
async def test_messages_table_has_correct_columns():
    conn = await asyncpg.connect(dsn=DB_DSN)
    try:
        rows = await conn.fetch(
            "SELECT column_name, data_type FROM information_schema.columns "
            "WHERE table_name = 'messages' ORDER BY ordinal_position"
        )
        columns = {r["column_name"]: r["data_type"] for r in rows}
        assert "id" in columns
        assert "thread_id" in columns
        assert "role" in columns
        assert "content" in columns
        assert "created_at" in columns
        assert columns["thread_id"] == "text"
        assert columns["role"] == "text"
    finally:
        await conn.close()
