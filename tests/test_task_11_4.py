from langchain_core.messages import HumanMessage, AIMessage
from agentia.graph import agent_node, MAX_ITERATIONS


def _state(iteration: int) -> dict:
    return {
        "messages": [HumanMessage(content="繼續")],
        "thread_id": "t1",
        "iteration_count": iteration,
    }


def test_agent_node_returns_truncation_at_max_iterations():
    result = agent_node(_state(MAX_ITERATIONS))
    msgs = result["messages"]
    assert len(msgs) == 1
    assert isinstance(msgs[0], AIMessage)
    assert len(msgs[0].content) > 0


def test_agent_node_does_not_increment_count_when_truncated():
    result = agent_node(_state(MAX_ITERATIONS))
    assert "iteration_count" not in result
