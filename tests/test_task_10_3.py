from langchain_core.messages import HumanMessage
from agentia.router import route_by_intent


def _state(intent: str, confidence: float) -> dict:
    return {
        "messages": [HumanMessage(content="hi")],
        "thread_id": "t1",
        "intent": intent,
        "intent_confidence": confidence,
    }


def test_low_confidence_always_routes_to_clarify():
    assert route_by_intent(_state("chitchat", 0.5)) == "clarify"
    assert route_by_intent(_state("tool_use", 0.0)) == "clarify"


def test_confidence_at_threshold_routes_by_intent():
    assert route_by_intent(_state("chitchat", 0.6)) == "chitchat"


def test_high_confidence_routes_by_intent():
    assert route_by_intent(_state("chitchat", 0.9)) == "chitchat"
    assert route_by_intent(_state("tool_use", 0.8)) == "tool_use"
    assert route_by_intent(_state("knowledge_query", 0.7)) == "knowledge_query"
    assert route_by_intent(_state("writing_assist", 0.95)) == "writing_assist"


def test_unknown_intent_falls_back_to_clarify():
    assert route_by_intent(_state("unknown_intent", 0.9)) == "clarify"
