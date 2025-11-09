"""Structured Logging with Context"""

import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime
from typing import Any, Dict, Optional

from pythonjsonlogger import jsonlogger

# Context variables for request tracing
correlation_id_var: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)
request_path_var: ContextVar[Optional[str]] = ContextVar("request_path", default=None)
user_session_var: ContextVar[Optional[str]] = ContextVar("user_session", default=None)


class ContextualJsonFormatter(jsonlogger.JsonFormatter):
    """JSON formatter that includes correlation ID and request context"""

    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)

        # Add timestamp
        log_record["timestamp"] = datetime.utcnow().isoformat()

        # Add correlation ID if available
        correlation_id = correlation_id_var.get()
        if correlation_id:
            log_record["correlation_id"] = correlation_id

        # Add request path if available
        request_path = request_path_var.get()
        if request_path:
            log_record["request_path"] = request_path

        # Add user session if available
        user_session = user_session_var.get()
        if user_session:
            log_record["session_id"] = user_session

        # Add log level
        log_record["level"] = record.levelname


def setup_logging(level: str = "INFO"):
    """Setup structured logging with context support

    Args:
        level: Either a standard logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
               or an environment name (development, production) which will be mapped
    """
    # Map environment names to logging levels
    level_mapping = {
        "development": "DEBUG",
        "dev": "DEBUG",
        "production": "INFO",
        "prod": "INFO",
        "staging": "INFO",
        "test": "DEBUG",
    }

    # Convert environment to logging level if needed
    log_level = level_mapping.get(level.lower(), level.upper())

    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Remove existing handlers
    logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    formatter = ContextualJsonFormatter("%(timestamp)s %(level)s %(name)s %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get logger with contextual formatting"""
    return logging.getLogger(name)


def log_with_context(logger: logging.Logger, level: str, message: str, **kwargs: Any):
    """Log with additional context"""
    extra = {
        "correlation_id": correlation_id_var.get(),
        "request_path": request_path_var.get(),
        "session_id": user_session_var.get(),
        **kwargs,
    }

    log_func = getattr(logger, level.lower())
    log_func(message, extra=extra)
