import structlog
from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.prebuilt import ToolNode
from langgraph.types import interrupt

from agentia.models import AgentState
from agentia.llm import get_llm_provider

log = structlog.get_logger()

MAX_ITERATIONS = 10
_SYS_PROMPT = (
    "你是一個專業的助理，請務必使用『繁體中文』回答所有問題。\n\n"
    "【工具使用順序】\n"
    "遇到任何知識性問題時，必須先呼叫 retrieve_knowledge 工具搜尋知識庫。\n"
    "只有在 retrieve_knowledge 回傳空結果（chunks 為空字串）時，才可改用 web_search。\n"
    "retrieve_knowledge 有結果時，請優先引用其內容作答，並標明來源文件，禁止跳過直接使用 web_search。\n\n"
    "【web_search 回傳格式】\n"
    "將結果整合為自然語言回答，以 [來源標題](URL) 格式標註引用，不要直接列出連結清單。"
)


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


# Read-only tools that never need human approval
_SAFE_TOOLS = {"retrieve_knowledge", "web_search", "get_current_datetime", "search_history"}


def confirm_tool_node(state: AgentState) -> dict:
    last_msg = state["messages"][-1]
    tool_calls = getattr(last_msg, "tool_calls", None) or []

    if not tool_calls:
        return {}

    tc = tool_calls[0]
    if tc["name"] in _SAFE_TOOLS:
        return {}

    approved = interrupt({"tool": tc["name"], "args": tc.get("args", {})})

    if approved is True:
        return {}

    content = (
        "Tool call confirmation timeout."
        if approved == "timeout"
        else "Action cancelled by user."
    )
    return {
        "messages": [
            ToolMessage(content=content, tool_call_id=item["id"])
            for item in tool_calls
        ]
    }


def after_confirm_edge(state: AgentState) -> str:
    last_msg = state["messages"][-1]
    return "agent" if isinstance(last_msg, ToolMessage) else "tools"


def react_edge(state: AgentState) -> str:
    if state.get("iteration_count", 0) >= MAX_ITERATIONS:
        return "save_context"
    last_msg = state["messages"][-1]
    if getattr(last_msg, "tool_calls", None):
        return "tools"
    return "save_context"


def _extract_retrieved_context(messages: list) -> str | None:
    """Return the chunks text from the most recent retrieve_knowledge ToolMessage, if any."""
    import json as _json
    # Build a map from tool_call_id → tool name
    id_to_name: dict[str, str] = {}
    for msg in messages:
        for tc in getattr(msg, "tool_calls", None) or []:
            id_to_name[tc["id"]] = tc["name"]
    # Find the latest retrieve_knowledge result
    for msg in reversed(messages):
        if isinstance(msg, ToolMessage):
            name = id_to_name.get(getattr(msg, "tool_call_id", ""), "")
            if name == "retrieve_knowledge":
                try:
                    data = _json.loads(msg.content)
                    return data.get("chunks") or None
                except Exception:
                    pass
    return None


def _make_agent(tools: list[BaseTool]):
    def _agent(state: AgentState) -> dict:
        iteration = state.get("iteration_count", 0)
        log.info("node.enter", node="agent", thread_id=state["thread_id"], iteration=iteration)
        if iteration >= MAX_ITERATIONS:
            msg = AIMessage(content="已達最大迭代次數，對話已截斷，請重新提問。")
            log.warning("agent.truncated", thread_id=state["thread_id"])
            return {"messages": [msg]}
        llm = get_llm_provider()
        runnable = llm.bind_tools(tools) if tools else llm._llm

        extra: list = []
        ctx = _extract_retrieved_context(state["messages"])
        if ctx:
            extra = [SystemMessage(content=f"以下為參考資料：\n\n{ctx}")]

        messages = [SystemMessage(content=_SYS_PROMPT)] + extra + state["messages"]
        response = runnable.invoke(messages)
        log.info("node.exit", node="agent", thread_id=state["thread_id"])
        return {"messages": [response], "iteration_count": iteration + 1}
    return _agent


def build_chat_subgraph(tools: list[BaseTool] | None = None):
    """General Chat Agent subgraph (no router, no checkpointer — used inside Supervisor)."""
    tools = tools or []

    builder = StateGraph(AgentState)

    builder.add_node("load_context", load_context_node)
    builder.add_node("agent", _make_agent(tools))
    builder.add_node("confirm_tool", confirm_tool_node)
    builder.add_node("tools", ToolNode(tools, handle_tool_errors=True))
    builder.add_node("save_context", save_context_node)

    builder.add_edge(START, "load_context")
    builder.add_edge("load_context", "agent")
    builder.add_conditional_edges(
        "agent",
        react_edge,
        {"tools": "confirm_tool", "save_context": "save_context"},
    )
    builder.add_conditional_edges(
        "confirm_tool",
        after_confirm_edge,
        {"tools": "tools", "agent": "agent"},
    )
    builder.add_edge("tools", "agent")
    builder.add_edge("save_context", END)

    return builder.compile()


def build_graph(checkpointer: BaseCheckpointSaver = None, tools: list[BaseTool] | None = None):
    from agentia.supervisor import build_supervisor
    return build_supervisor(checkpointer=checkpointer, tools=tools)


graph = build_graph()
