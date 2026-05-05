from langchain_ollama import ChatOllama
from agentia.config import LLM_BASE_URL, LLM_MODEL


def get_llm() -> ChatOllama:
    return ChatOllama(
        model=LLM_MODEL,
        base_url=LLM_BASE_URL,
        streaming=True,
    )
