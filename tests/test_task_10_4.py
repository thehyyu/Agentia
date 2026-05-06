from langchain_core.messages import HumanMessage, AIMessage
from agentia.router import clarify_node


def _state() -> dict:
    return {
        "messages": [HumanMessage(content="嗯")],
        "thread_id": "t1",
        "intent": "",
        "intent_confidence": 0.0,
    }


def test_clarify_node_returns_ai_message():
    result = clarify_node(_state())
    msgs = result["messages"]
    assert len(msgs) == 1
    assert isinstance(msgs[0], AIMessage)


def test_clarify_node_message_asks_user_to_rephrase():
    result = clarify_node(_state())
    content = result["messages"][0].content
    assert len(content) > 0
