import logging
from datetime import datetime, timezone
from typing import Any, Optional


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Set up a logger with the specified name and log level.
    
    Args:
        name: Logger name, typically __name__ from the calling module
        level: Logging level (default: logging.INFO)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger


def log_event(logger: logging.Logger, event: str, **kwargs: Any) -> None:
    """
    Log an event with additional context data.
    
    Args:
        logger: Logger instance to use
        event: Event description
        **kwargs: Additional context data to include in the log
    """
    context = " | ".join(f"{k}={v}" for k, v in kwargs.items()) if kwargs else ""
    message = f"{event} | timestamp={datetime.now(timezone.utc).isoformat()}"
    if context:
        message += f" | {context}"
    logger.info(message)


def log_error(logger: logging.Logger, error: str, **kwargs: Any) -> None:
    """
    Log an error with additional context data.
    
    Args:
        logger: Logger instance to use
        error: Error description
        **kwargs: Additional context data to include in the log
    """
    context = " | ".join(f"{k}={v}" for k, v in kwargs.items()) if kwargs else ""
    message = f"{error} | timestamp={datetime.now(timezone.utc).isoformat()}"
    if context:
        message += f" | {context}"
    logger.error(message)


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
    context_parts = [f"worker_id={worker_id}", f"nudge_count={nudge_count}"]
    if reason:
        context_parts.append(f"reason={reason}")
    
    if kwargs:
        context_parts.extend(f"{k}={v}" for k, v in kwargs.items())
    
    context = " | ".join(context_parts)
    message = f"Nudge event | {context} | timestamp={datetime.now(timezone.utc).isoformat()}"
    logger.info(message)
