import structlog
from pydantic import BaseModel, Field
from langchain_core.messages import AIMessage, SystemMessage
from langchain_ollama import ChatOllama

from agentia.models import AgentState
from agentia.config import LLM_BASE_URL, ROUTER_MODEL

log = structlog.get_logger()

_router_llm = ChatOllama(model=ROUTER_MODEL, base_url=LLM_BASE_URL)

CONFIDENCE_THRESHOLD = 0.6
VALID_INTENTS = frozenset({"chitchat", "tool_use", "knowledge_query", "writing_assist", "moon_phase"})

_ROUTER_SYSTEM = SystemMessage(content=(
    "Classify the user's latest message into EXACTLY one of these intents:\n"
    "- chitchat: casual conversation, greetings, small talk, sharing daily life\n"
    "- tool_use: requests that need tools (time, search, calculations)\n"
    "- knowledge_query: questions seeking factual information or explanation\n"
    "- writing_assist: writing, editing, translation, summarization tasks\n"
    "- moon_phase: any question about the current moon phase, lunar cycle, or moon-related topics\n\n"
    "Reply with the intent label and a confidence score 0.0–1.0. "
    "Do not invent other intent names."
))


class IntentClassification(BaseModel):
    intent: str = Field(description="One of: chitchat, tool_use, knowledge_query, writing_assist")
    confidence: float = Field(ge=0.0, le=1.0)


def router_node(state: AgentState) -> dict:
    log.info("node.enter", node="router", thread_id=state["thread_id"])
    structured_llm = _router_llm.with_structured_output(IntentClassification)
    result: IntentClassification = structured_llm.invoke([_ROUTER_SYSTEM] + list(state["messages"]))
    log.info(
        "node.exit",
        node="router",
        thread_id=state["thread_id"],
        intent=result.intent,
        confidence=result.confidence,
    )
    return {"intent": result.intent, "intent_confidence": result.confidence}


def clarify_node(state: AgentState) -> dict:
    log.info("node.enter", node="clarify", thread_id=state["thread_id"])
    msg = AIMessage(content="抱歉，我不太確定您的需求，能請您重新描述一下嗎？")
    log.info("node.exit", node="clarify", thread_id=state["thread_id"])
    return {"messages": [msg]}


def route_by_intent(state: AgentState) -> str:
    confidence = state.get("intent_confidence", 0.0)
    if confidence < CONFIDENCE_THRESHOLD:
        return "clarify"
    intent = state.get("intent", "")
    return intent if intent in VALID_INTENTS else "clarify"
