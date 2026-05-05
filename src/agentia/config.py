import os
from dotenv import load_dotenv

load_dotenv()

LLM_PROVIDER: str = os.environ.get("LLM_PROVIDER", "ollama")
LLM_MODEL: str = os.environ.get("LLM_MODEL", "qwen2.5:32b")
LLM_BASE_URL: str = os.environ.get("LLM_BASE_URL", "http://localhost:11434")

REDIS_URL: str = os.environ.get("REDIS_URL", "redis://localhost:6379")
DATABASE_URL: str = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://agentia:agentia@localhost:5432/agentia",
)
# psycopg (used by langgraph checkpointer) doesn't use the +asyncpg prefix
PSYCOPG_DATABASE_URL: str = DATABASE_URL.replace("+asyncpg", "")

LANGFUSE_PUBLIC_KEY: str = os.environ.get("LANGFUSE_PUBLIC_KEY", "")
LANGFUSE_SECRET_KEY: str = os.environ.get("LANGFUSE_SECRET_KEY", "")
LANGFUSE_HOST: str = os.environ.get("LANGFUSE_HOST", "http://localhost:3000")
