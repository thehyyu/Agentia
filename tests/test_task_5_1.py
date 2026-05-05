from typing import Annotated, get_type_hints
from langgraph.graph.message import add_messages
from agentia.models import AgentState

def test_task_5_1_agent_state_schema():
    """
    RED -> GREEN: Verify AgentState has 'messages' with add_messages reducer and 'thread_id'.
    """
    hints = get_type_hints(AgentState, include_extras=True)
    
    # Verify 'messages' exists and has correct metadata
    assert "messages" in hints
    messages_hint = hints["messages"]
    assert hasattr(messages_hint, "__metadata__")
    assert messages_hint.__metadata__[0] == add_messages
    
    # Verify 'thread_id' exists
    assert "thread_id" in hints
    assert hints["thread_id"] == str
