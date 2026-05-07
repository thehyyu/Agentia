from langgraph.checkpoint.memory import InMemorySaver
from agentia.graph import build_graph


def test_task_8_1_build_graph_accepts_checkpointer():
    """
    Task 8.1: build_graph() 接受 checkpointer 並正確配置到 compiled graph。
    實際注入發生在 FastAPI lifespan，module-level graph 無 checkpointer 是預期行為。
    """
    saver = InMemorySaver()
    g = build_graph(checkpointer=saver)
    assert g.checkpointer is saver


def test_task_8_1_default_graph_has_no_checkpointer():
    """build_graph() 不帶 checkpointer 引數時，回傳的 graph 不帶 checkpointer。"""
    g = build_graph()
    assert g.checkpointer is None
