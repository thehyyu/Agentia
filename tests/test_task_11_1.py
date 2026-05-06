from agentia.models import AgentState


def test_agent_state_declares_tool_results():
    assert "tool_results" in AgentState.__annotations__


def test_agent_state_declares_iteration_count():
    assert "iteration_count" in AgentState.__annotations__
