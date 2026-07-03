"""
Structured logging implementation using structlog.

Provides configuration and utilities for structured logging with both
console (human-readable) and JSON (machine-readable) formatters.
"""

import logging
import sys
from typing import Any

import structlog


def configure_structured_logging(
    log_level: str = "INFO",
    json_format: bool = False,
    service_name: str = "ai-research-copilot",
) -> None:
    """Configure structlog with console and JSON formatters.

    Sets up structlog processors and formatters for structured logging.
    Supports both human-readable console output and JSON output for
    production environments.

    Args:
        log_level: Minimum log level to output (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        json_format: If True, use JSON formatter. If False, use console formatter.
        service_name: Name of the service to include in log entries.
    """
    log_level_upper = log_level.upper()
    numeric_level = getattr(logging, log_level_upper, logging.INFO)

    logging.basicConfig(
        format="%(message)s",
        level=numeric_level,
        stream=sys.stdout,
    )

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if service_name:
        def add_service_name(
            logger: Any, method_name: str, event_dict: dict[str, Any]
        ) -> dict[str, Any]:
            event_dict["service"] = service_name
            return event_dict

        shared_processors.append(add_service_name)

    if json_format:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(numeric_level)

    for logger_name in ["uvicorn", "uvicorn.error", "uvicorn.access"]:
        uvicorn_logger = logging.getLogger(logger_name)
        uvicorn_logger.handlers.clear()
        uvicorn_logger.addHandler(handler)
        uvicorn_logger.setLevel(numeric_level)

    structlog_logger = structlog.get_logger()
    structlog_logger.info(
        "Structured logging configured",
        log_level=log_level_upper,
        json_format=json_format,
    )


def get_logger(name: str | None = None) -> structlog.BoundLogger:
    """Get a structlog logger instance.

    Creates a new bound logger with the specified name for organized
    log output.

    Args:
        name: Optional name to bind to the logger. Typically the module name.

    Returns:
        A bound structlog logger instance.

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing started", item_count=10)
    """
    if name:
        return structlog.get_logger(name)
    return structlog.get_logger()
