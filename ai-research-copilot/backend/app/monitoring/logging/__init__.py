"""
Structured logging module.

Provides configuration and utilities for structured logging using structlog
with console and JSON formatters.
"""

from app.monitoring.logging.structured import configure_structured_logging, get_logger

__all__ = ["configure_structured_logging", "get_logger"]
