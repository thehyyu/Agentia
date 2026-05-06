from agentia.observability import make_langfuse_handler


def test_make_langfuse_handler_returns_none_when_keys_not_set(monkeypatch):
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "")
    handler = make_langfuse_handler()
    assert handler is None


def test_make_langfuse_handler_returns_handler_when_keys_set(monkeypatch):
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
    monkeypatch.setenv("LANGFUSE_HOST", "http://localhost:3000")
    handler = make_langfuse_handler()
    assert handler is not None
