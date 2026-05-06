import structlog
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.base import BaseCheckpointSaver

from agentia.models import AgentState
from agentia.llm import get_llm_provider

log = structlog.get_logger()


def agent_node(state: AgentState) -> AgentState:
    log.info("node.enter", node="agent", thread_id=state["thread_id"])
    llm = get_llm_provider()
    
    # 注入系統提示詞，確保輸出為繁體中文
    sys_msg = SystemMessage(content="你是一個專業的助理，請務必使用『繁體中文』回答所有問題。")
    messages = [sys_msg] + state["messages"]
    
    response = llm.invoke(messages)
    log.info("node.exit", node="agent", thread_id=state["thread_id"])
    return {"messages": [response]}


def build_graph(checkpointer: BaseCheckpointSaver = None):
    """
    建立並編譯 LangGraph。
    學習點：透過參數注入 checkpointer，讓同一個 Graph 定義可以適配不同的儲存後端。
    """
    builder = StateGraph(AgentState)
    builder.add_node("agent", agent_node)
    builder.add_edge(START, "agent")
    builder.add_edge("agent", END)
    
    return builder.compile(checkpointer=checkpointer)

# 為了保持回溯相容性，我們先提供一個無持久化能力的預設實例
# 在 FastAPI 啟動後，我們會用具備 Postgres 能力的實例替換它
graph = build_graph()
