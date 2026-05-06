from agentia.llm import OllamaProvider, LLMProvider


def test_ollama_provider_satisfies_llm_provider_protocol():
    provider = OllamaProvider()
    assert isinstance(provider, LLMProvider)


def test_ollama_provider_exposes_underlying_model():
    provider = OllamaProvider()
    assert provider.model_name == "qwen2.5:32b" or isinstance(provider.model_name, str)
