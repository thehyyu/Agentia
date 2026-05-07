"""Task 17: pgvector extension + chunks table + Ollama embedding verification."""
import pytest
import asyncpg
import httpx

from agentia.config import DATABASE_URL, LLM_BASE_URL


@pytest.fixture(autouse=True)
async def apply_migration():
    dsn = DATABASE_URL.replace("+asyncpg", "")
    conn = await asyncpg.connect(dsn=dsn)
    with open("migrations/002_pgvector.sql") as f:
        sql = f.read()
    for statement in sql.split(";"):
        s = statement.strip()
        if s:
            await conn.execute(s)
    yield conn
    await conn.close()


@pytest.mark.asyncio
async def test_17_1_vector_extension_is_enabled(apply_migration):
    conn = apply_migration
    row = await conn.fetchrow(
        "SELECT extname FROM pg_extension WHERE extname = 'vector'"
    )
    assert row is not None, "pgvector extension is not installed"


@pytest.mark.asyncio
async def test_17_2_chunks_table_has_correct_schema(apply_migration):
    conn = apply_migration
    rows = await conn.fetch(
        """
        SELECT column_name, udt_name
        FROM information_schema.columns
        WHERE table_name = 'chunks'
        ORDER BY ordinal_position
        """
    )
    columns = {r["column_name"]: r for r in rows}

    assert "id" in columns
    assert "doc_id" in columns
    assert "content" in columns
    assert "embedding" in columns
    assert "created_at" in columns
    assert columns["embedding"]["udt_name"] == "vector"


@pytest.mark.asyncio
async def test_17_2_can_insert_and_retrieve_embedding(apply_migration):
    conn = apply_migration
    fake_embedding = [0.1] * 1024

    await conn.execute(
        "INSERT INTO chunks (doc_id, content, embedding) VALUES ($1, $2, $3::vector)",
        "test-doc-001",
        "This is a test chunk.",
        str(fake_embedding),
    )
    row = await conn.fetchrow(
        "SELECT content FROM chunks WHERE doc_id = $1", "test-doc-001"
    )
    assert row["content"] == "This is a test chunk."

    await conn.execute("DELETE FROM chunks WHERE doc_id = $1", "test-doc-001")


@pytest.mark.asyncio
async def test_17_4_ollama_embedding_returns_1024_dims():
    async with httpx.AsyncClient(base_url=LLM_BASE_URL, timeout=60) as client:
        resp = await client.post(
            "/api/embeddings",
            json={"model": "bge-m3", "prompt": "hello world"},
        )
    assert resp.status_code == 200, f"Ollama returned {resp.status_code}: {resp.text}"
    embedding = resp.json()["embedding"]
    assert len(embedding) == 1024, f"Expected 1024 dims, got {len(embedding)}"
