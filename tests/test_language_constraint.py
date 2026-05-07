import pytest
from langchain_core.messages import HumanMessage
from agentia.graph import build_graph as _build_graph
graph = _build_graph()

@pytest.mark.integration
@pytest.mark.asyncio
async def test_agent_responds_in_traditional_chinese():
    """
    驗證 Agent 是否遵守系統提示詞，使用繁體中文回答。
    """
    input_state = {
        "messages": [HumanMessage(content="你是誰？請用一句話自我介紹。")],
        "thread_id": "test-lang-check"
    }
    
    result = await graph.ainvoke(input_state)
    response_text = result["messages"][-1].content
    
    # 簡單的繁體中文特徵檢查（例如檢查是否包含常見的簡體字，或是否包含繁體特有字）
    # 這裡我們檢查回覆內容是否不包含常見的簡體字，如 "体" (體), "说" (說)
    simplified_chars = ["体", "说", "谁", "请", "个"]
    found_simplified = [c for c in simplified_chars if c in response_text]
    
    print(f"\nAI 回覆: {response_text}")
    assert not found_simplified, f"發現簡體字: {found_simplified}"
    assert len(response_text) > 0
