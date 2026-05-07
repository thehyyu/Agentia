import pytest
from langchain_core.messages import AIMessage, ToolMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from agentia.graph import confirm_tool_node, after_confirm_edge
from agentia.models import AgentState

_TOOL_CALL = {"name": "send_email", "args": {"to": "test@example.com"}, "id": "call_1", "type": "tool_call"}


def _make_test_graph():
    def fake_agent(state):
        return {"messages": [AIMessage(content="", tool_calls=[_TOOL_CALL])]}

    def tools_stub(state):
        return {"messages": [ToolMessage(content="2026-05-06T00:00:00Z", tool_call_id="call_1")]}

    def agent_stub(state):
        return {"messages": [AIMessage(content="好的，已取消。")]}

    builder = StateGraph(AgentState)
    builder.add_node("fake_agent", fake_agent)
    builder.add_node("confirm_tool", confirm_tool_node)
    builder.add_node("tools_stub", tools_stub)
    builder.add_node("agent_stub", agent_stub)

    builder.add_edge(START, "fake_agent")
    builder.add_edge("fake_agent", "confirm_tool")
    builder.add_conditional_edges(
        "confirm_tool",
        after_confirm_edge,
        {"tools": "tools_stub", "agent": "agent_stub"},
    )
    builder.add_edge("tools_stub", END)
    builder.add_edge("agent_stub", END)

    return builder.compile(checkpointer=MemorySaver())


@pytest.mark.asyncio
async def test_confirm_tool_pauses_graph():
    graph = _make_test_graph()
    config = {"configurable": {"thread_id": "test-14-1a"}}

    async for _ in graph.astream_events(
        {"messages": [], "thread_id": "test-14-1a"}, config=config, version="v2"
    ):
        pass

    state = await graph.aget_state(config)
    assert state.next  # graph paused at confirm_tool


@pytest.mark.asyncio
async def test_confirm_tool_interrupt_payload():
    graph = _make_test_graph()
    config = {"configurable": {"thread_id": "test-14-1b"}}

    async for _ in graph.astream_events(
        {"messages": [], "thread_id": "test-14-1b"}, config=config, version="v2"
    ):
        pass

    state = await graph.aget_state(config)
    interrupts = [i for task in state.tasks for i in task.interrupts]
    assert len(interrupts) == 1
    assert interrupts[0].value["tool"] == "send_email"
    assert "args" in interrupts[0].value


@pytest.mark.asyncio
async def test_confirm_tool_approved_continues_to_tools():
    graph = _make_test_graph()
    config = {"configurable": {"thread_id": "test-14-1c"}}

    async for _ in graph.astream_events(
        {"messages": [], "thread_id": "test-14-1c"}, config=config, version="v2"
    ):
        pass

    async for _ in graph.astream_events(Command(resume=True), config=config, version="v2"):
        pass

    state = await graph.aget_state(config)
    assert not state.next
    assert any(isinstance(m, ToolMessage) for m in state.values["messages"])


@pytest.mark.asyncio
async def test_confirm_tool_rejected_injects_cancel_message():
    graph = _make_test_graph()
    config = {"configurable": {"thread_id": "test-14-1d"}}

    async for _ in graph.astream_events(
        {"messages": [], "thread_id": "test-14-1d"}, config=config, version="v2"
    ):
        pass

    async for _ in graph.astream_events(Command(resume=False), config=config, version="v2"):
        pass

    state = await graph.aget_state(config)
    assert not state.next
    tool_msgs = [m for m in state.values["messages"] if isinstance(m, ToolMessage)]
    assert tool_msgs
    assert "cancel" in tool_msgs[-1].content.lower()


@pytest.mark.asyncio
async def test_confirm_tool_timeout_injects_timeout_message():
    graph = _make_test_graph()
    config = {"configurable": {"thread_id": "test-14-1e"}}

    async for _ in graph.astream_events(
        {"messages": [], "thread_id": "test-14-1e"}, config=config, version="v2"
    ):
        pass

    async for _ in graph.astream_events(
        Command(resume="timeout"), config=config, version="v2"
    ):
        pass

    state = await graph.aget_state(config)
    assert not state.next
    tool_msgs = [m for m in state.values["messages"] if isinstance(m, ToolMessage)]
    assert tool_msgs
    assert "timeout" in tool_msgs[-1].content.lower()
