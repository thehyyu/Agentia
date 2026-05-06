from agentia.models import AgentState
from agentia.router import router_node
from langchain_core.messages import HumanMessage


def test_agent_state_has_intent_field():
    state: AgentState = {
        "messages": [],
        "thread_id": "t1",
        "intent": "chitchat",
        "intent_confidence": 0.9,
    }
    assert state["intent"] == "chitchat"
    assert state["intent_confidence"] == 0.9


def test_router_node_is_callable_with_agent_state():
    assert callable(router_node)
