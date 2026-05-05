import pytest
from typing import Annotated, get_type_hints
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph.message import add_messages
from agentia.models import AgentState

def test_agent_state_definition():
    """
    Task 5.1 TDD: Verify AgentState definition.
    It must be a TypedDict with 'messages' (Annotated with add_messages) and 'thread_id'.
    """
    # 1. Check keys existence
    # TypedDict.__annotations__ or get_type_hints can be used
    hints = get_type_hints(AgentState, include_extras=True)
    
    assert "messages" in hints
    assert "thread_id" in hints
    
    # 2. Check Annotated and reducer
    # The type should be Annotated[list[BaseMessage], add_messages]
    messages_hint = hints["messages"]
    # In Python 3.9+, Annotated types have __metadata__
    assert hasattr(messages_hint, "__metadata__")
    assert messages_hint.__metadata__[0] == add_messages
    
    # 3. Verify behavior (optional but good for TDD)
    state: AgentState = {
        "messages": [HumanMessage(content="hello")],
        "thread_id": "test-123"
    }
    assert state["thread_id"] == "test-123"
    assert len(state["messages"]) == 1

def test_agent_state_reducer_behavior():
    """
    Ensures that the reducer (add_messages) works as expected when merging states.
    This indirectly tests if the annotation is correctly interpreted by tools.
    """
    # Note: StateGraph uses this metadata. We can simulate the reducer logic.
    initial_msgs = [HumanMessage(content="hi")]
    new_msgs = [AIMessage(content="hello")]
    
    # add_messages is the reducer function
    merged = add_messages(initial_msgs, new_msgs)
    assert len(merged) == 2
    assert merged[0].content == "hi"
    assert merged[1].content == "hello"
