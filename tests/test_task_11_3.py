from langchain_core.messages import AIMessage, HumanMessage
from agentia.graph import react_edge


def _state(messages, iteration=0):
    return {
        "messages": messages,
        "thread_id": "t1",
        "iteration_count": iteration,
    }


def test_no_tool_calls_routes_to_save_context():
    msg = AIMessage(content="這是普通回覆")
    assert react_edge(_state([msg])) == "save_context"


def test_tool_calls_present_routes_to_tools():
    msg = AIMessage(
        content="",
        tool_calls=[{"name": "get_current_datetime", "args": {}, "id": "call_1"}],
    )
    assert react_edge(_state([msg])) == "tools"


def test_max_iterations_reached_routes_to_save_context_even_with_tool_calls():
    msg = AIMessage(
        content="",
        tool_calls=[{"name": "get_current_datetime", "args": {}, "id": "call_1"}],
    )
    assert react_edge(_state([msg], iteration=10)) == "save_context"
