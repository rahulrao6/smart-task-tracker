import json
import logging
import os
import sys
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, Optional


class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs logs in JSON format."""

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as JSON.
        
        Args:
            record: Log record to format
            
        Returns:
            JSON-formatted log string
        """
        log_data: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        return json.dumps(log_data)


class TextFormatter(logging.Formatter):
    """Custom formatter for plain text logs with color support for console."""

    COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[35m",
        "RESET": "\033[0m",
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as colored text.
        
        Args:
            record: Log record to format
            
        Returns:
            Formatted log string
        """
        timestamp = datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat()
        color = self.COLORS.get(record.levelname, "")
        reset = self.COLORS["RESET"]

        message = f"{timestamp} - {color}{record.levelname}{reset} - {record.name} - {record.getMessage()}"

        if record.exc_info:
            message += f"\n{self.formatException(record.exc_info)}"

        return message


def setup_logger(
    name: str,
    level: int = logging.INFO,
    log_dir: Optional[str] = None,
    enable_file_rotation: bool = True,
    max_file_size: int = 10 * 1024 * 1024,
    backup_count: int = 5,
    json_format: bool = False,
) -> logging.Logger:
    """
    Set up a comprehensive logger with file rotation and multiple output formats.

    Args:
        name: Logger name, typically __name__ from the calling module
        level: Logging level (default: logging.INFO)
        log_dir: Directory to store log files (default: ./logs)
        enable_file_rotation: Enable rotating file handler (default: True)
        max_file_size: Maximum log file size in bytes (default: 10MB)
        backup_count: Number of backup log files to keep (default: 5)
        json_format: Use JSON format for output (default: False)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        return logger

    if log_dir is None:
        log_dir = os.path.join(os.getcwd(), "logs")

    Path(log_dir).mkdir(parents=True, exist_ok=True)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    if json_format:
        console_formatter = JSONFormatter()
    else:
        console_formatter = TextFormatter()

    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    if enable_file_rotation:
        log_file = os.path.join(log_dir, f"{name}.log")
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
        )
        file_handler.setLevel(level)

        file_formatter = JSONFormatter() if json_format else TextFormatter()
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


def setup_application_logger(
    log_dir: Optional[str] = None,
    level: int = logging.INFO,
    json_format: bool = False,
) -> logging.Logger:
    """
    Set up the main application logger with file rotation.

    Args:
        log_dir: Directory to store log files (default: ./logs)
        level: Logging level (default: logging.INFO)
        json_format: Use JSON format for output (default: False)

    Returns:
        Configured application logger
    """
    return setup_logger(
        "app",
        level=level,
        log_dir=log_dir,
        enable_file_rotation=True,
        json_format=json_format,
    )


class _ContextFilter(logging.Filter):
    """Filter to inject extra context data into log records."""

    def __init__(self, extra_data: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.extra_data = extra_data or {}

    def filter(self, record: logging.LogRecord) -> bool:
        if self.extra_data:
            record.extra_data = self.extra_data
        return True


def log_event(logger: logging.Logger, event: str, **kwargs: Any) -> None:
    """
    Log an event with additional context data.

    Args:
        logger: Logger instance to use
        event: Event description
        **kwargs: Additional context data to include in the log
    """
    extra_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **kwargs,
    }

    log_filter = _ContextFilter(extra_data)
    logger.addFilter(log_filter)
    try:
        logger.info(event)
    finally:
        logger.removeFilter(log_filter)


def log_error(logger: logging.Logger, error: str, **kwargs: Any) -> None:
    """
    Log an error with additional context data.

    Args:
        logger: Logger instance to use
        error: Error description
        **kwargs: Additional context data to include in the log
    """
    extra_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **kwargs,
    }

    log_filter = _ContextFilter(extra_data)
    logger.addFilter(log_filter)
    try:
        logger.error(error)
    finally:
        logger.removeFilter(log_filter)


def log_warning(logger: logging.Logger, warning: str, **kwargs: Any) -> None:
    """
    Log a warning with additional context data.

    Args:
        logger: Logger instance to use
        warning: Warning description
        **kwargs: Additional context data to include in the log
    """
    extra_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **kwargs,
    }

    log_filter = _ContextFilter(extra_data)
    logger.addFilter(log_filter)
    try:
        logger.warning(warning)
    finally:
        logger.removeFilter(log_filter)


def log_debug(logger: logging.Logger, debug: str, **kwargs: Any) -> None:
    """
    Log a debug message with additional context data.

    Args:
        logger: Logger instance to use
        debug: Debug message description
        **kwargs: Additional context data to include in the log
    """
    extra_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **kwargs,
    }

    log_filter = _ContextFilter(extra_data)
    logger.addFilter(log_filter)
    try:
        logger.debug(debug)
    finally:
        logger.removeFilter(log_filter)


def log_nudge(logger: logging.Logger, worker_id: str, nudge_count: int, reason: Optional[str] = None, **kwargs: Any) -> None:
    """
    Log a nudge event for loop prevention tracking.

    Args:
        logger: Logger instance to use
        worker_id: ID of the worker being nudged
        nudge_count: Current nudge count for this worker
        reason: Optional reason for the nudge
        **kwargs: Additional context data to include in the log
    """
    extra_data = {
        "event_type": "nudge",
        "worker_id": worker_id,
        "nudge_count": nudge_count,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    if reason:
        extra_data["reason"] = reason

    extra_data.update(kwargs)

    log_filter = _ContextFilter(extra_data)
    logger.addFilter(log_filter)
    try:
        logger.info(f"Nudge event for worker {worker_id}")
    finally:
        logger.removeFilter(log_filter)
