import structlog
from pydantic import BaseModel, Field
from langchain_core.messages import AIMessage

from agentia.models import AgentState
from agentia.llm import get_llm_provider

log = structlog.get_logger()

CONFIDENCE_THRESHOLD = 0.6
VALID_INTENTS = frozenset({"chitchat", "tool_use", "knowledge_query", "writing_assist"})


class IntentClassification(BaseModel):
    intent: str = Field(description="One of: chitchat, tool_use, knowledge_query, writing_assist, clarify")
    confidence: float = Field(ge=0.0, le=1.0)
