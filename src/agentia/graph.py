import structlog
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END

from agentia.models import AgentState
from agentia.llm import get_llm

log = structlog.get_logger()


def agent_node(state: AgentState) -> AgentState:
    log.info("node.enter", node="agent", thread_id=state["thread_id"])
    llm = get_llm()
    
    # 注入系統提示詞，確保輸出為繁體中文
    sys_msg = SystemMessage(content="你是一個專業的助理，請務必使用『繁體中文』回答所有問題。")
    messages = [sys_msg] + state["messages"]
    
    response = llm.invoke(messages)
    log.info("node.exit", node="agent", thread_id=state["thread_id"])
    return {"messages": [response]}


def build_graph() -> StateGraph:
    builder = StateGraph(AgentState)
    builder.add_node("agent", agent_node)
    builder.add_edge(START, "agent")
    builder.add_edge("agent", END)
    return builder.compile()


graph = build_graph()
