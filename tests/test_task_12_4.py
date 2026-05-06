from langchain_core.tools import tool
from agentia.graph import build_graph


def test_adding_tool_does_not_change_graph_node_structure():
    @tool
    def extra_tool(query: str) -> str:
        """An extra tool added later."""
        return f"result: {query}"

    g_empty = build_graph(tools=[])
    g_with_tool = build_graph(tools=[extra_tool])

    assert set(g_empty.nodes.keys()) == set(g_with_tool.nodes.keys())


def test_all_tools_registered_in_build_graph():
    from agentia.tools import get_current_datetime, search_history, ALL_TOOLS
    assert get_current_datetime in ALL_TOOLS
    assert search_history in ALL_TOOLS
