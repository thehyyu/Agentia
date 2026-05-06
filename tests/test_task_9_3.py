import pytest
from agentia.llm import get_llm_provider, OllamaProvider, LLMProvider


def test_get_llm_provider_returns_ollama_by_default(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    provider = get_llm_provider()
    assert isinstance(provider, OllamaProvider)


def test_get_llm_provider_returns_llm_provider_instance(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    provider = get_llm_provider()
    assert isinstance(provider, LLMProvider)


def test_get_llm_provider_raises_for_unknown_provider(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    with pytest.raises(ValueError, match="openai"):
        get_llm_provider()
