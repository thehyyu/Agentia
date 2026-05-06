from typing import Annotated
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode


class _S(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


def _tool_graph(tools):
    builder = StateGraph(_S)
    builder.add_node("tools", ToolNode(tools, handle_tool_errors=True))
    builder.add_edge(START, "tools")
    builder.add_edge("tools", END)
    return builder.compile()


def test_tool_node_catches_exception_and_returns_tool_message():
    @tool
    def always_fails() -> str:
        """Always raises."""
        raise RuntimeError("tool exploded")

    g = _tool_graph([always_fails])
    state = {
        "messages": [
            AIMessage(
                content="",
                tool_calls=[{"name": "always_fails", "args": {}, "id": "call_1"}],
            )
        ]
    }
    result = g.invoke(state)
    tool_msgs = [m for m in result["messages"] if isinstance(m, ToolMessage)]
    assert len(tool_msgs) == 1
    assert tool_msgs[0].status == "error"


def test_tool_node_error_message_contains_exception_info():
    @tool
    def divide_by_zero(x: int) -> float:
        """Divides by zero."""
        return x / 0

    g = _tool_graph([divide_by_zero])
    state = {
        "messages": [
            AIMessage(
                content="",
                tool_calls=[{"name": "divide_by_zero", "args": {"x": 1}, "id": "call_2"}],
            )
        ]
    }
    result = g.invoke(state)
    tool_msgs = [m for m in result["messages"] if isinstance(m, ToolMessage)]
    assert len(tool_msgs[0].content) > 0
