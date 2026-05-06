import structlog
from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.tools import BaseTool
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.prebuilt import ToolNode

from agentia.models import AgentState
from agentia.llm import get_llm_provider
from agentia.router import router_node, clarify_node, route_by_intent

log = structlog.get_logger()

MAX_ITERATIONS = 10
_SYS_PROMPT = "你是一個專業的助理，請務必使用『繁體中文』回答所有問題。"


def load_context_node(state: AgentState) -> dict:
    log.info("node.enter", node="load_context", thread_id=state["thread_id"])
    log.info("node.exit", node="load_context", thread_id=state["thread_id"])
    return {}


def agent_node(state: AgentState) -> dict:
    iteration = state.get("iteration_count", 0)
    log.info("node.enter", node="agent", thread_id=state["thread_id"], iteration=iteration)

    if iteration >= MAX_ITERATIONS:
        msg = AIMessage(content="已達最大迭代次數，對話已截斷，請重新提問。")
        log.warn("agent.truncated", thread_id=state["thread_id"])
        return {"messages": [msg]}

    llm = get_llm_provider()
    messages = [SystemMessage(content=_SYS_PROMPT)] + state["messages"]
    response = llm.invoke(messages)
    log.info("node.exit", node="agent", thread_id=state["thread_id"])
    return {"messages": [response], "iteration_count": iteration + 1}


def save_context_node(state: AgentState) -> dict:
    log.info("node.enter", node="save_context", thread_id=state["thread_id"])
    log.info("node.exit", node="save_context", thread_id=state["thread_id"])
    return {}


def react_edge(state: AgentState) -> str:
    if state.get("iteration_count", 0) >= MAX_ITERATIONS:
        return "save_context"
    last_msg = state["messages"][-1]
    if getattr(last_msg, "tool_calls", None):
        return "tools"
    return "save_context"


def build_graph(checkpointer: BaseCheckpointSaver = None, tools: list[BaseTool] | None = None):
    tools = tools or []

    builder = StateGraph(AgentState)

    builder.add_node("load_context", load_context_node)
    builder.add_node("router", router_node)
    builder.add_node("agent", agent_node)
    builder.add_node("tools", ToolNode(tools))
    builder.add_node("save_context", save_context_node)
    builder.add_node("clarify", clarify_node)

    builder.add_edge(START, "load_context")
    builder.add_edge("load_context", "router")
    builder.add_conditional_edges(
        "router",
        route_by_intent,
        {
            "chitchat": "agent",
            "tool_use": "agent",
            "knowledge_query": "agent",
            "writing_assist": "agent",
            "clarify": "clarify",
        },
    )
    builder.add_conditional_edges(
        "agent",
        react_edge,
        {"tools": "tools", "save_context": "save_context"},
    )
    builder.add_edge("tools", "agent")
    builder.add_edge("clarify", END)
    builder.add_edge("save_context", END)

    return builder.compile(checkpointer=checkpointer)


graph = build_graph()
