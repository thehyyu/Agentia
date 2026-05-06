import structlog

log = structlog.get_logger()


def process_graph_event(event: dict) -> dict | None:
    """Process a single astream_events event.

    Returns a WebSocket message dict to send, or None to skip.
    Side-effects: logs on_tool_end events.
    """
    kind = event.get("event")

    if kind == "on_chat_model_stream":
        token = event["data"]["chunk"].content
        if token:
            return {"type": "token", "content": token}
        return None

    if kind == "on_tool_end":
        log.info(
            "tool.end",
            tool=event.get("name"),
            output=str(event.get("data", {}).get("output", ""))[:200],
        )
        return None

    return None
