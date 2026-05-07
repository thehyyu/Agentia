import pytest
from structlog.testing import capture_logs
from langchain_core.messages import HumanMessage
from agentia.graph import build_graph as _build_graph
graph = _build_graph()

@pytest.mark.integration
@pytest.mark.asyncio
async def test_task_5_3_node_logging():
    """
    Task 5.3 TDD: 驗證 Node 執行時是否有正確噴出 structlog。
    """
    input_state = {
        "messages": [HumanMessage(content="Hi, how are you today? Just saying hello!")],
        "thread_id": "test-logging-5-3"
    }
    
    # 使用 structlog 提供的工具攔截日誌
    with capture_logs() as logs:
        await graph.ainvoke(input_state)
    
    # 驗證是否包含進入日誌
    enter_log = next(
        (l for l in logs if l.get("event") == "node.enter" and l.get("node") == "agent"), 
        None
    )
    assert enter_log is not None, "缺少 node.enter 日誌"
    assert enter_log["thread_id"] == "test-logging-5-3"
    
    # 驗證是否包含離開日誌
    exit_log = next(
        (l for l in logs if l.get("event") == "node.exit" and l.get("node") == "agent"), 
        None
    )
    assert exit_log is not None, "缺少 node.exit 日誌"
    assert exit_log["thread_id"] == "test-logging-5-3"
