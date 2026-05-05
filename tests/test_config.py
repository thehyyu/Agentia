import importlib
import sys
import os
import pytest


@pytest.fixture()
def clean_config():
    """Reload config module with controlled env vars."""
    env_keys = [
        "LLM_PROVIDER", "LLM_MODEL", "LLM_BASE_URL",
        "REDIS_URL", "DATABASE_URL",
        "LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_HOST",
    ]
    original = {k: os.environ.pop(k, None) for k in env_keys}
    if "agentia.config" in sys.modules:
        del sys.modules["agentia.config"]
    yield
    for k, v in original.items():
        if v is not None:
            os.environ[k] = v
    if "agentia.config" in sys.modules:
        del sys.modules["agentia.config"]


def test_default_llm_provider(clean_config):
    import agentia.config as cfg
    assert cfg.LLM_PROVIDER == "ollama"


def test_default_llm_model(clean_config):
    import agentia.config as cfg
    assert cfg.LLM_MODEL == "qwen2.5:32b"


def test_default_llm_base_url(clean_config):
    import agentia.config as cfg
    assert cfg.LLM_BASE_URL == "http://localhost:11434"


def test_env_var_overrides_default(clean_config, monkeypatch):
    monkeypatch.setenv("LLM_MODEL", "mistral:v0.3")
    import agentia.config as cfg
    assert cfg.LLM_MODEL == "mistral:v0.3"
