import json
import structlog
from agentia.logging import setup_logging


def test_log_output_is_valid_json(capsys):
    setup_logging()
    log = structlog.get_logger()
    log.info("probe")
    out = capsys.readouterr().out
    json.loads(out)  # raises if not valid JSON


def test_log_output_contains_timestamp_and_level(capsys):
    setup_logging()
    log = structlog.get_logger()
    log.info("probe")
    data = json.loads(capsys.readouterr().out)
    assert "timestamp" in data
    assert data["level"] == "info"


def test_bound_fields_appear_in_json(capsys):
    setup_logging()
    log = structlog.get_logger().bind(thread_id="t-abc")
    log.info("probe")
    data = json.loads(capsys.readouterr().out)
    assert data["thread_id"] == "t-abc"
