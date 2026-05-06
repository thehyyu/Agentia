from datetime import datetime
from agentia.tools import get_current_datetime


def test_get_current_datetime_returns_iso8601_string():
    result = get_current_datetime.invoke({})
    datetime.fromisoformat(result)  # raises if not valid ISO 8601


def test_get_current_datetime_includes_timezone():
    result = get_current_datetime.invoke({})
    assert "+" in result or result.endswith("Z") or "UTC" in result or result.endswith("+00:00")
