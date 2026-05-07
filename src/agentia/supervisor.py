import structlog
from langchain_core.tools import BaseTool
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.base import BaseCheckpointSaver

from agentia.models import AgentState
from agentia.router import router_node, clarify_node
from agentia.moon_phase import build_moon_phase_graph

log = structlog.get_logger()

CONFIDENCE_THRESHOLD = 0.6


def _route(state: AgentState) -> str:
    confidence = state.get("intent_confidence", 0.0)
    if confidence < CONFIDENCE_THRESHOLD:
        destination = "clarify"
    else:
        intent = state.get("intent", "")
        destination = "moon_phase" if intent == "moon_phase" else "general_chat"
    log.info("supervisor.route", thread_id=state.get("thread_id"), handled_by=destination)
    return destination


def build_supervisor(
    checkpointer: BaseCheckpointSaver = None,
    tools: list[BaseTool] | None = None,
):
    from agentia.graph import build_chat_subgraph  # lazy to avoid circular import
    tools = tools or []
    chat_subgraph = build_chat_subgraph(tools=tools)
    moon_subgraph = build_moon_phase_graph()

    builder = StateGraph(AgentState)
    builder.add_node("router", router_node)
    builder.add_node("general_chat", chat_subgraph)
    builder.add_node("moon_phase", moon_subgraph)
    builder.add_node("clarify", clarify_node)

    builder.add_edge(START, "router")
    builder.add_conditional_edges(
        "router",
        _route,
        {
            "general_chat": "general_chat",
            "moon_phase": "moon_phase",
            "clarify": "clarify",
        },
    )
    builder.add_edge("general_chat", END)
    builder.add_edge("moon_phase", END)
    builder.add_edge("clarify", END)

    return builder.compile(checkpointer=checkpointer)
