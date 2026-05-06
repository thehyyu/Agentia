from agentia.graph import build_graph


def test_compiled_graph_contains_all_required_nodes():
    g = build_graph()
    node_names = set(g.nodes.keys())
    expected = {"load_context", "router", "agent", "tools", "save_context", "clarify"}
    assert expected.issubset(node_names)


def test_build_graph_accepts_tools_list():
    g = build_graph(tools=[])
    assert g is not None
