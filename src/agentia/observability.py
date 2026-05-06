import os


def make_langfuse_handler():
    """Return a LangfuseCallbackHandler if credentials are configured, else None.

    Langfuse v4 reads LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST
    from environment variables automatically.
    """
    public_key = os.environ.get("LANGFUSE_PUBLIC_KEY", "")
    secret_key = os.environ.get("LANGFUSE_SECRET_KEY", "")

    if not public_key or not secret_key:
        return None

    from langfuse.langchain import CallbackHandler
    return CallbackHandler()
