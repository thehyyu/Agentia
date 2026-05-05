import structlog
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END

from agentia.models import AgentState
from agentia.llm import get_llm

log = structlog.get_logger()


def agent_node(state: AgentState) -> AgentState:
    log.info("node.enter", node="agent", thread_id=state["thread_id"])
    llm = get_llm()
    response = llm.invoke(state["messages"])
    log.info("node.exit", node="agent", thread_id=state["thread_id"])
    return {"messages": [response]}


def build_graph() -> StateGraph:
    builder = StateGraph(AgentState)
    builder.add_node("agent", agent_node)
    builder.add_edge(START, "agent")
    builder.add_edge("agent", END)
    return builder.compile()


graph = build_graph()
