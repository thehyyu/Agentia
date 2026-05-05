import pytest
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from agentia.main import app
from agentia import graph as graph_module

@pytest.mark.asyncio
async def test_task_8_2_graph_uses_postgres_checkpointer_in_lifespan():
    """
    Task 8.2 TDD (GREEN): 驗證在 FastAPI 生命週期內，Graph 是否正確換裝為 AsyncPostgresSaver。
    學習點：手動調用 app.router.lifespan_context 可以在測試中模擬應用啟動。
    """
    # 避免依賴外部套件，直接使用 FastAPI 內建的 lifespan 處理
    async with app.router.lifespan_context(app):
        # 此時 graph_module.graph 應該已經在 main.py 的 lifespan 中被替換
        assert isinstance(graph_module.graph.checkpointer, AsyncPostgresSaver), \
            f"啟動後預期為 AsyncPostgresSaver, 但得到的是 {type(graph_module.graph.checkpointer)}"
        print("\n驗證成功：Graph 已成功注入 AsyncPostgresSaver。")
