import logging
from io import StringIO

import pytest

from src.app.utils.logging import log_error, log_event, log_nudge, setup_logger


@pytest.fixture
def test_logger():
    """Fixture to create a test logger."""
    return setup_logger("test_logger", level=logging.INFO)


def test_setup_logger():
    """Test that setup_logger creates a logger with correct configuration."""
    logger = setup_logger("test_setup_logger", level=logging.DEBUG)
    
    assert logger.name == "test_setup_logger"
    assert logger.level == logging.DEBUG
    assert len(logger.handlers) > 0


def test_setup_logger_handler_format():
    """Test that the logger handler has the correct format."""
    logger = setup_logger("test_format_logger", level=logging.INFO)
    
    handler = logger.handlers[0]
    formatter = handler.formatter
    
    assert formatter is not None
    assert "%(asctime)s" in formatter._fmt
    assert "%(name)s" in formatter._fmt
    assert "%(levelname)s" in formatter._fmt
    assert "%(message)s" in formatter._fmt


def test_log_event(test_logger, caplog):
    """Test that log_event logs messages correctly."""
    with caplog.at_level(logging.INFO):
        log_event(test_logger, "Test event occurred")
    
    assert "Test event occurred" in caplog.text
    assert "timestamp=" in caplog.text


def test_log_event_with_context(test_logger, caplog):
    """Test that log_event includes context data."""
    with caplog.at_level(logging.INFO):
        log_event(test_logger, "User action", user_id=123, action="login")
    
    assert "User action" in caplog.text
    assert "user_id=123" in caplog.text
    assert "action=login" in caplog.text
    assert "timestamp=" in caplog.text


def test_log_error(test_logger, caplog):
    """Test that log_error logs error messages correctly."""
    with caplog.at_level(logging.ERROR):
        log_error(test_logger, "An error occurred")
    
    assert "An error occurred" in caplog.text
    assert "timestamp=" in caplog.text
    assert caplog.records[0].levelno == logging.ERROR


def test_log_error_with_context(test_logger, caplog):
    """Test that log_error includes context data."""
    with caplog.at_level(logging.ERROR):
        log_error(test_logger, "Database error", error_code=500, table="tasks")
    
    assert "Database error" in caplog.text
    assert "error_code=500" in caplog.text
    assert "table=tasks" in caplog.text
    assert "timestamp=" in caplog.text
    assert caplog.records[0].levelno == logging.ERROR


def test_log_event_multiple_calls(test_logger, caplog):
    """Test multiple log_event calls."""
    with caplog.at_level(logging.INFO):
        log_event(test_logger, "Event 1")
        log_event(test_logger, "Event 2", context="data")
        log_event(test_logger, "Event 3")
    
    assert len(caplog.records) == 3
    assert "Event 1" in caplog.text
    assert "Event 2" in caplog.text
    assert "Event 3" in caplog.text


def test_log_nudge(test_logger, caplog):
    """Test that log_nudge logs nudge events correctly."""
    with caplog.at_level(logging.INFO):
        log_nudge(test_logger, "worker-123", 1)
    
    assert "Nudge event" in caplog.text
    assert "worker_id=worker-123" in caplog.text
    assert "nudge_count=1" in caplog.text
    assert "timestamp=" in caplog.text


def test_log_nudge_with_reason(test_logger, caplog):
    """Test that log_nudge includes reason when provided."""
    with caplog.at_level(logging.INFO):
        log_nudge(test_logger, "worker-456", 2, reason="CI failure")
    
    assert "Nudge event" in caplog.text
    assert "worker_id=worker-456" in caplog.text
    assert "nudge_count=2" in caplog.text
    assert "reason=CI failure" in caplog.text
    assert "timestamp=" in caplog.text


def test_log_nudge_with_context(test_logger, caplog):
    """Test that log_nudge includes additional context data."""
    with caplog.at_level(logging.INFO):
        log_nudge(test_logger, "worker-789", 3, reason="merge conflict", branch="main", status="pending")
    
    assert "Nudge event" in caplog.text
    assert "worker_id=worker-789" in caplog.text
    assert "nudge_count=3" in caplog.text
    assert "reason=merge conflict" in caplog.text
    assert "branch=main" in caplog.text
    assert "status=pending" in caplog.text
    assert "timestamp=" in caplog.text


def test_log_nudge_without_reason(test_logger, caplog):
    """Test that log_nudge works without a reason."""
    with caplog.at_level(logging.INFO):
        log_nudge(test_logger, "worker-111", 5, extra_info="test_data")
    
    assert "Nudge event" in caplog.text
    assert "worker_id=worker-111" in caplog.text
    assert "nudge_count=5" in caplog.text
    assert "extra_info=test_data" in caplog.text
    assert "timestamp=" in caplog.text


def test_log_nudge_level(test_logger, caplog):
    """Test that log_nudge logs at INFO level."""
    with caplog.at_level(logging.INFO):
        log_nudge(test_logger, "worker-999", 1)
    
    assert len(caplog.records) == 1
    assert caplog.records[0].levelno == logging.INFO


def test_log_nudge_multiple_calls(test_logger, caplog):
    """Test multiple log_nudge calls with incrementing counts."""
    with caplog.at_level(logging.INFO):
        log_nudge(test_logger, "worker-multi", 1, reason="first")
        log_nudge(test_logger, "worker-multi", 2, reason="second")
        log_nudge(test_logger, "worker-multi", 3, reason="third")
    
    assert len(caplog.records) == 3
    assert "nudge_count=1" in caplog.text
    assert "nudge_count=2" in caplog.text
    assert "nudge_count=3" in caplog.text
