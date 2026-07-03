"""
Monitoring and observability module for the AI Research Copilot.

Provides Prometheus metrics, OpenTelemetry tracing, and structured logging
for comprehensive system monitoring and observability.
"""

from app.monitoring.metrics.prometheus import MetricsCollector, metrics
from app.monitoring.tracing.tracer import TracingService
from app.monitoring.logging.structured import configure_structured_logging, get_logger

__all__ = [
    "MetricsCollector",
    "metrics",
    "TracingService",
    "configure_structured_logging",
    "get_logger",
]
