import pytest
from structlog.testing import capture_logs
from langchain_core.messages import HumanMessage
from agentia.graph import graph

@pytest.mark.integration
@pytest.mark.asyncio
async def test_graph_node_logs_enter_exit():
    """
    Task 5.3 TDD: Verify that the agent node logs 'node.enter' and 'node.exit'.
    """
    input_state = {
        "messages": [HumanMessage(content="Hello")],
        "thread_id": "test-logs-53"
    }
    
    with capture_logs() as logs:
        await graph.ainvoke(input_state)
    
    # Check for enter log
    enter_log = next((l for l in logs if l.get("event") == "node.enter" and l.get("node") == "agent"), None)
    assert enter_log is not None
    assert enter_log["thread_id"] == "test-logs-53"
    
    # Check for exit log
    exit_log = next((l for l in logs if l.get("event") == "node.exit" and l.get("node") == "agent"), None)
    assert exit_log is not None
    assert exit_log["thread_id"] == "test-logs-53"
