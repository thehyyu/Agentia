import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_check_redis_returns_true_when_ping_succeeds():
    mock_redis = AsyncMock()
    mock_redis.ping.return_value = True
    mock_redis.aclose = AsyncMock()
    with patch("agentia.health.aioredis.from_url", return_value=mock_redis):
        from agentia.health import check_redis
        result = await check_redis()
    assert result is True


@pytest.mark.asyncio
async def test_check_redis_returns_false_on_connection_error():
    mock_redis = AsyncMock()
    mock_redis.ping.side_effect = ConnectionError("refused")
    mock_redis.aclose = AsyncMock()
    with patch("agentia.health.aioredis.from_url", return_value=mock_redis):
        from agentia.health import check_redis
        result = await check_redis()
    assert result is False


@pytest.mark.asyncio
async def test_check_postgres_returns_true_when_query_succeeds():
    mock_conn = AsyncMock()
    mock_conn.fetchval.return_value = 1
    mock_conn.close = AsyncMock()
    with patch("agentia.health.asyncpg.connect", return_value=mock_conn):
        from agentia.health import check_postgres
        result = await check_postgres()
    assert result is True


@pytest.mark.asyncio
async def test_check_postgres_returns_false_on_error():
    with patch("agentia.health.asyncpg.connect", side_effect=OSError("no route")):
        from agentia.health import check_postgres
        result = await check_postgres()
    assert result is False


@pytest.mark.asyncio
async def test_check_ollama_returns_true_when_api_tags_200():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_client = AsyncMock()
    mock_client.get.return_value = mock_resp
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    with patch("agentia.health.httpx.AsyncClient", return_value=mock_client):
        from agentia.health import check_ollama
        result = await check_ollama()
    assert result is True


@pytest.mark.asyncio
async def test_check_ollama_returns_false_on_connection_error():
    mock_client = AsyncMock()
    mock_client.get.side_effect = Exception("connection refused")
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    with patch("agentia.health.httpx.AsyncClient", return_value=mock_client):
        from agentia.health import check_ollama
        result = await check_ollama()
    assert result is False
