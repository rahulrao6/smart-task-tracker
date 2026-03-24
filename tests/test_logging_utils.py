import logging
from io import StringIO

import pytest

from src.app.utils.logging import log_error, log_event, setup_logger


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
