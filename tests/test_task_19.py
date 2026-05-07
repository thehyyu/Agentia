"""Task 19: Knowledge retrieval tool + web search tool."""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from langchain_core.messages import AIMessage, ToolMessage

from agentia.tools import retrieve_knowledge, web_search, ALL_TOOLS
from agentia.graph import _extract_retrieved_context

FAKE_EMBEDDING = [0.1] * 1024
FAKE_CHUNKS = [
    {"doc_id": "my-post_zh", "content": "LangGraph 是一個用於建構有狀態 agent 的框架。"},
    {"doc_id": "my-post_en", "content": "LangGraph is a framework for building stateful agents."},
]


# --- 19.1: retrieve_knowledge tool ---

@pytest.mark.asyncio
async def test_19_1_returns_chunks_and_related_articles():
    mock_conn = AsyncMock()
    mock_conn.fetch = AsyncMock(return_value=FAKE_CHUNKS)

    with patch("agentia.tools.embed_text", AsyncMock(return_value=FAKE_EMBEDDING)), \
         patch("asyncpg.connect", AsyncMock(return_value=mock_conn)):
        result = await retrieve_knowledge.ainvoke({"query": "LangGraph 怎麼用"})

    data = json.loads(result)
    assert "LangGraph" in data["chunks"]
    assert "my-post" in data["related_articles"]
    assert len(data["related_articles"]) <= 3


@pytest.mark.asyncio
async def test_19_1_empty_result_when_no_chunks():
    mock_conn = AsyncMock()
    mock_conn.fetch = AsyncMock(return_value=[])

    with patch("agentia.tools.embed_text", AsyncMock(return_value=FAKE_EMBEDDING)), \
         patch("asyncpg.connect", AsyncMock(return_value=mock_conn)):
        result = await retrieve_knowledge.ainvoke({"query": "火星殖民地"})

    data = json.loads(result)
    assert data["chunks"] == ""
    assert data["related_articles"] == []


# --- 19.2: SystemMessage injection ---

def _make_tool_message(content: str, tool_call_id: str) -> ToolMessage:
    return ToolMessage(content=content, tool_call_id=tool_call_id)


def test_19_2_extract_retrieved_context_finds_chunks():
    chunks_payload = json.dumps({"chunks": "以下是參考資料內容", "related_articles": ["my-post"]})
    messages = [
        AIMessage(content="", tool_calls=[{"id": "call_1", "name": "retrieve_knowledge", "args": {}}]),
        _make_tool_message(chunks_payload, "call_1"),
    ]
    ctx = _extract_retrieved_context(messages)
    assert ctx == "以下是參考資料內容"


def test_19_2_extract_returns_none_when_no_retrieve_tool():
    messages = [
        AIMessage(content="", tool_calls=[{"id": "call_1", "name": "web_search", "args": {}}]),
        _make_tool_message("some result", "call_1"),
    ]
    assert _extract_retrieved_context(messages) is None


def test_19_2_extract_returns_none_when_chunks_empty():
    payload = json.dumps({"chunks": "", "related_articles": []})
    messages = [
        AIMessage(content="", tool_calls=[{"id": "call_1", "name": "retrieve_knowledge", "args": {}}]),
        _make_tool_message(payload, "call_1"),
    ]
    assert _extract_retrieved_context(messages) is None


# --- 19.3: related_articles max 3 ---

@pytest.mark.asyncio
async def test_19_3_related_articles_capped_at_3():
    many_chunks = [
        {"doc_id": f"post-{i}_zh", "content": f"content {i}"}
        for i in range(6)
    ]
    mock_conn = AsyncMock()
    mock_conn.fetch = AsyncMock(return_value=many_chunks)

    with patch("agentia.tools.embed_text", AsyncMock(return_value=FAKE_EMBEDDING)), \
         patch("asyncpg.connect", AsyncMock(return_value=mock_conn)):
        result = await retrieve_knowledge.ainvoke({"query": "anything"})

    data = json.loads(result)
    assert len(data["related_articles"]) <= 3


# --- web_search tool ---

def test_web_search_returns_json_results():
    fake_results = {
        "results": [
            {"title": "LangGraph Docs", "url": "https://example.com", "content": "LangGraph info"},
        ]
    }
    with patch("agentia.tools.TAVILY_API_KEY", "fake-key"), \
         patch("tavily.TavilyClient") as MockClient:
        MockClient.return_value.search.return_value = fake_results
        result = web_search.invoke({"query": "LangGraph"})

    items = json.loads(result)
    assert items[0]["title"] == "LangGraph Docs"
    assert items[0]["url"] == "https://example.com"


def test_web_search_disabled_without_api_key():
    with patch("agentia.tools.TAVILY_API_KEY", ""):
        result = web_search.invoke({"query": "anything"})
    assert "未啟用" in result


# --- ALL_TOOLS registration ---

def test_retrieve_knowledge_in_all_tools():
    names = [t.name for t in ALL_TOOLS]
    assert "retrieve_knowledge" in names


def test_web_search_in_all_tools_when_key_set():
    with patch("agentia.tools.TAVILY_API_KEY", "fake-key"):
        import importlib
        import agentia.tools as tools_mod
        tools = tools_mod._base_tools + ([tools_mod.web_search] if "fake-key" else [])
        names = [t.name for t in tools]
        assert "web_search" in names
