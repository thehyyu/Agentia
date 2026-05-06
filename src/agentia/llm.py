import os
from typing import Any, AsyncIterator, Protocol, runtime_checkable

from langchain_ollama import ChatOllama
from langchain_core.messages import BaseMessage

from agentia.config import LLM_BASE_URL, LLM_MODEL


@runtime_checkable
class LLMProvider(Protocol):
    def invoke(self, messages: list[BaseMessage]) -> BaseMessage: ...
    async def astream(self, messages: list[BaseMessage]) -> AsyncIterator[BaseMessage]: ...
    def with_structured_output(self, schema: type) -> Any: ...


class OllamaProvider:
    def __init__(self) -> None:
        self._llm = ChatOllama(model=LLM_MODEL, base_url=LLM_BASE_URL, streaming=True)
        self.model_name: str = LLM_MODEL

    def invoke(self, messages: list[BaseMessage]) -> BaseMessage:
        return self._llm.invoke(messages)

    async def astream(self, messages: list[BaseMessage]) -> AsyncIterator[BaseMessage]:
        async for chunk in self._llm.astream(messages):
            yield chunk

    def with_structured_output(self, schema: type) -> Any:
        return self._llm.with_structured_output(schema)


def get_llm_provider() -> LLMProvider:
    provider = os.environ.get("LLM_PROVIDER", "ollama")
    if provider == "ollama":
        return OllamaProvider()
    raise ValueError(f"Unknown LLM_PROVIDER: {provider!r}")


def get_llm() -> ChatOllama:
    return ChatOllama(
        model=LLM_MODEL,
        base_url=LLM_BASE_URL,
        streaming=True,
    )
