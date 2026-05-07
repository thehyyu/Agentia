import pytest
from langchain_core.messages import HumanMessage, AIMessage
from agentia.graph import build_graph as _build_graph
graph = _build_graph()

@pytest.mark.integration
@pytest.mark.asyncio
async def test_graph_execution_single_node():
    """
    Task 5.2 TDD: Verify the single-node StateGraph execution.
    Behavior: Given messages, it should return an AgentState with an additional AI message.
    """
    input_state = {
        "messages": [HumanMessage(content="Hello, what is your name?")],
        "thread_id": "test-graph-52"
    }
    
    # We use ainvoke for the compiled graph
    result = await graph.ainvoke(input_state)
    
    assert "messages" in result
    assert len(result["messages"]) > 1
    assert isinstance(result["messages"][-1], AIMessage)
    assert len(result["messages"][-1].content) > 0

def test_graph_structure():
    """
    Verify the graph has the expected node and edges.
    """
    # The compiled graph has nodes and edges info
    # In langgraph, we can check graph.nodes
    assert "general_chat" in graph.nodes
    assert "moon_phase" in graph.nodes
    assert "router" in graph.nodes
    # Check edges (this is slightly more complex in compiled graphs, 
    # but we can at least check for the existence of the node)
