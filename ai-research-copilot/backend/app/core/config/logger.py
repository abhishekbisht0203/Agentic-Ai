"""
Structured logging configuration using structlog.

Provides JSON-formatted logging with context binding for observability.
"""

import sys
import logging
from typing import Any

import structlog
from structlog.types import Processor


def get_loggers(
    level: str = "INFO",
    log_format: str = "json",
    log_file: str | None = None,
) -> dict[str, Any]:
    """
    Configure and return structlog loggers.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_format: Output format ('json' or 'console').
        log_file: Optional file path for log output.

    Returns:
        Dictionary of configured loggers.
    """
    # Validate log level
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Shared processors for all loggers
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    # Format processors based on output format
    if log_format == "json":
        format_processors: list[Processor] = [
            structlog.processors.JSONRenderer()
        ]
    else:
        format_processors = [
            structlog.dev.ConsoleRenderer(colors=True)
        ]

    # Configure structlog
    structlog.configure(
        processors=shared_processors + format_processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard logging
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]

    if log_file:
        # Add file handler for persistent logging
        file_handler = logging.FileHandler(log_file)
        handlers.append(file_handler)

    logging.basicConfig(
        format="%(message)s",
        level=numeric_level,
        handlers=handlers,
        force=True,
    )

    return {
        "structlog": structlog,
        "get_logger": structlog.get_logger,
    }


def setup_logging(
    level: str = "INFO",
    log_format: str = "json",
    log_file: str | None = None,
) -> None:
    """
    Setup application-wide logging configuration.

    Args:
        level: Log level string.
        log_format: Output format ('json' or 'console').
        log_file: Optional file path for logging.
    """
    get_loggers(level=level, log_format=log_format, log_file=log_file)


# Module-level logger instance
setup_logging()
logger = structlog.get_logger()