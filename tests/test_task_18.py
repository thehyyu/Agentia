"""Task 18: Knowledge ingestion from Echoforge blog API (posts + projects, bilingual)."""
import pytest
from pytest_httpx import HTTPXMock
from unittest.mock import MagicMock, AsyncMock
from fastapi.testclient import TestClient

from agentia.main import app
from agentia.dependencies import get_db_pool
from agentia.ingest import chunk_text

LONG_ZH = " ".join(["字"] * 1200)
LONG_EN = " ".join(["word"] * 1200)
FAKE_EMBEDDING = [0.1] * 1024
OLLAMA_EMBED_URL = "http://localhost:11434/api/embeddings"


def fake_response(slug: str, lang: str, content_type: str = "post") -> dict:
    content = LONG_ZH if lang == "zh" else LONG_EN
    return {
        content_type: {
            "slug": slug,
            "title": "Test",
            "title_zh": "測試",
            "title_en": "Test",
            "content": content,
            "url_zh": f"/zh/{content_type}s/{slug}",
            "url_en": f"/en/{content_type}s/{slug}",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        }
    }


def add_embed_mocks(httpx_mock: HTTPXMock, count: int):
    """Add `count` fake Ollama embedding responses."""
    for _ in range(count):
        httpx_mock.add_response(
            url=OLLAMA_EMBED_URL,
            json={"embedding": FAKE_EMBEDDING},
        )


def chunks_for(text: str) -> int:
    return len(chunk_text(text))


# --- Pure unit tests ---

def test_18_3_chunk_text_splits_long_text():
    assert len(chunk_text(" ".join(["word"] * 1200))) > 1


def test_18_3_chunk_text_short_text_is_single_chunk():
    assert len(chunk_text("Short text.")) == 1


def test_18_3_chunks_have_overlap():
    text = " ".join([str(i) for i in range(600)])
    chunks = chunk_text(text, size=500, overlap=50)
    assert chunks[0].split()[-50:] == chunks[1].split()[:50]


# --- Endpoint tests ---

@pytest.fixture()
def client():
    # psycopg AsyncConnectionPool uses `async with pool.connection() as conn:`
    mock_cursor = AsyncMock()
    mock_cursor.execute = AsyncMock()
    mock_cursor.executemany = AsyncMock()
    mock_cursor.fetchall = AsyncMock(return_value=[])
    mock_cursor.__aenter__ = AsyncMock(return_value=mock_cursor)
    mock_cursor.__aexit__ = AsyncMock(return_value=None)

    mock_conn = AsyncMock()
    mock_conn.cursor = MagicMock(return_value=mock_cursor)
    mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_conn.__aexit__ = AsyncMock(return_value=None)

    mock_pool = MagicMock()
    mock_pool.connection = MagicMock(return_value=mock_conn)

    app.dependency_overrides[get_db_pool] = lambda: mock_pool
    yield TestClient(app), mock_pool, mock_conn, mock_cursor
    app.dependency_overrides.clear()


def test_18_1_ingest_post_both_languages(httpx_mock: HTTPXMock, client):
    test_client, *_ = client
    httpx_mock.add_response(
        url="https://thehyyu-blog.vercel.app/api/posts/abc123?lang=zh",
        json=fake_response("abc123", "zh"),
    )
    httpx_mock.add_response(
        url="https://thehyyu-blog.vercel.app/api/posts/abc123?lang=en",
        json=fake_response("abc123", "en"),
    )
    total_chunks = chunks_for(LONG_ZH) + chunks_for(LONG_EN)
    add_embed_mocks(httpx_mock, total_chunks)

    response = test_client.post("/api/knowledge/ingest", json={"slug": "abc123"})

    assert response.status_code == 200
    data = response.json()
    assert data["slug"] == "abc123"
    assert data["type"] == "post"
    assert data["zh"]["chunks"] > 1
    assert data["en"]["chunks"] > 1


def test_18_1_ingest_project_both_languages(httpx_mock: HTTPXMock, client):
    test_client, *_ = client
    httpx_mock.add_response(
        url="https://thehyyu-blog.vercel.app/api/projects/tangram?lang=zh",
        json=fake_response("tangram", "zh", "project"),
    )
    httpx_mock.add_response(
        url="https://thehyyu-blog.vercel.app/api/projects/tangram?lang=en",
        json=fake_response("tangram", "en", "project"),
    )
    add_embed_mocks(httpx_mock, chunks_for(LONG_ZH) + chunks_for(LONG_EN))

    response = test_client.post(
        "/api/knowledge/ingest", json={"slug": "tangram", "type": "project"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "project"
    assert data["zh"]["chunks"] > 1
    assert data["en"]["chunks"] > 1


def test_18_5_doc_id_uses_slug_and_lang(httpx_mock: HTTPXMock, client):
    test_client, _, _, mock_cursor = client
    httpx_mock.add_response(
        url="https://thehyyu-blog.vercel.app/api/posts/abc123?lang=zh",
        json=fake_response("abc123", "zh"),
    )
    httpx_mock.add_response(
        url="https://thehyyu-blog.vercel.app/api/posts/abc123?lang=en",
        json=fake_response("abc123", "en"),
    )
    add_embed_mocks(httpx_mock, chunks_for(LONG_ZH) + chunks_for(LONG_EN))

    test_client.post("/api/knowledge/ingest", json={"slug": "abc123"})

    assert mock_cursor.executemany.call_count == 2
    doc_ids = {call.args[1][0][0] for call in mock_cursor.executemany.call_args_list}
    assert "abc123_zh" in doc_ids
    assert "abc123_en" in doc_ids


def test_18_missing_language_is_skipped(httpx_mock: HTTPXMock, client):
    test_client, *_ = client
    httpx_mock.add_response(
        url="https://thehyyu-blog.vercel.app/api/posts/abc123?lang=zh",
        json=fake_response("abc123", "zh"),
    )
    httpx_mock.add_response(
        url="https://thehyyu-blog.vercel.app/api/posts/abc123?lang=en",
        json={"post": {**fake_response("abc123", "en")["post"], "content": ""}},
    )
    add_embed_mocks(httpx_mock, chunks_for(LONG_ZH))

    response = test_client.post("/api/knowledge/ingest", json={"slug": "abc123"})

    assert response.status_code == 200
    data = response.json()
    assert data["zh"]["chunks"] > 0
    assert data["en"] is None


def test_18_7_sync_ingests_new_and_skips_existing(httpx_mock: HTTPXMock, client):
    test_client, _, _, mock_cursor = client
    mock_cursor.fetchall = AsyncMock(return_value=[{"doc_id": "existing_zh"}])

    httpx_mock.add_response(
        url="https://thehyyu-blog.vercel.app/api/posts",
        json={"posts": [{"slug": "abc123"}, {"slug": "existing"}], "count": 2},
    )
    httpx_mock.add_response(
        url="https://thehyyu-blog.vercel.app/api/projects",
        json={"projects": [], "count": 0},
    )
    httpx_mock.add_response(
        url="https://thehyyu-blog.vercel.app/api/posts/abc123?lang=zh",
        json=fake_response("abc123", "zh"),
    )
    httpx_mock.add_response(
        url="https://thehyyu-blog.vercel.app/api/posts/abc123?lang=en",
        json=fake_response("abc123", "en"),
    )
    add_embed_mocks(httpx_mock, chunks_for(LONG_ZH) + chunks_for(LONG_EN))

    response = test_client.post("/api/knowledge/sync")

    assert response.status_code == 200
    data = response.json()
    assert data["ingested"] == 1
    assert data["skipped"] == 1


def test_18_6_returns_404_when_slug_not_found(httpx_mock: HTTPXMock, client):
    test_client, *_ = client
    httpx_mock.add_response(
        url="https://thehyyu-blog.vercel.app/api/posts/notexist?lang=zh",
        status_code=404,
    )

    response = test_client.post("/api/knowledge/ingest", json={"slug": "notexist"})
    assert response.status_code == 404
