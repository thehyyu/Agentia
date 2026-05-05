from langchain_core.messages import HumanMessage, AIMessage
from agentia.models import AgentState


def test_agent_state_has_required_keys():
    state: AgentState = {"messages": [], "thread_id": "t-1"}
    assert "messages" in state
    assert "thread_id" in state


def test_messages_reducer_appends():
    from langgraph.graph.message import add_messages
    existing = [HumanMessage(content="hi")]
    new = [AIMessage(content="hello")]
    result = add_messages(existing, new)
    assert len(result) == 2
    assert result[0].content == "hi"
    assert result[1].content == "hello"


def test_messages_reducer_deduplicates_by_id():
    from langgraph.graph.message import add_messages
    msg = HumanMessage(content="hi", id="msg-1")
    updated = HumanMessage(content="hi updated", id="msg-1")
    result = add_messages([msg], [updated])
    assert len(result) == 1
    assert result[0].content == "hi updated"
