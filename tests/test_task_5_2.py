import pytest
from langchain_core.messages import HumanMessage, AIMessage
from agentia.graph import build_graph as _build_graph
graph = _build_graph()

@pytest.mark.integration
@pytest.mark.asyncio
async def test_task_5_2_graph_execution():
    """
    Task 5.2 TDD: 驗證單節點 Graph 是否能產生 AI 回覆。
    """
    # 準備初始狀態
    initial_state = {
        "messages": [HumanMessage(content="你好，請問你是誰？")],
        "thread_id": "test-5-2"
    }

    # 執行 Graph (這會呼叫真實的 Ollama)
    final_state = await graph.ainvoke(initial_state)

    # 驗證結果
    # 1. 訊息清單應該被更新了（原本 1 條 + AI 回覆 1 條 = 2 條）
    assert len(final_state["messages"]) >= 2
    
    # 2. 最後一條訊息應該是 AI 產生的
    last_message = final_state["messages"][-1]
    assert isinstance(last_message, AIMessage)
    assert len(last_message.content) > 0
    
    print(f"\nAI 回覆內容: {last_message.content}")

def test_task_5_2_graph_structure():
    """
    驗證 Graph 的結構是否包含預期的節點。
    """
    # 檢查編譯後的 Graph 節點清單
    # 注意：graph.nodes 在 LangGraph 中是一個 dict
    assert "general_chat" in graph.nodes
    assert "router" in graph.nodes
