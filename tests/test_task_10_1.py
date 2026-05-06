import pytest
from pydantic import ValidationError
from agentia.router import IntentClassification


def test_intent_classification_stores_intent_and_confidence():
    c = IntentClassification(intent="chitchat", confidence=0.9)
    assert c.intent == "chitchat"
    assert c.confidence == 0.9


def test_confidence_must_be_between_0_and_1():
    with pytest.raises(ValidationError):
        IntentClassification(intent="chitchat", confidence=1.5)
    with pytest.raises(ValidationError):
        IntentClassification(intent="chitchat", confidence=-0.1)


def test_all_valid_intents_are_accepted():
    for intent in ("chitchat", "tool_use", "knowledge_query", "writing_assist", "clarify"):
        c = IntentClassification(intent=intent, confidence=0.8)
        assert c.intent == intent
