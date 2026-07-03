"""
OpenTelemetry tracing module.

Provides distributed tracing capabilities using OpenTelemetry for
tracking request flows across services and identifying performance bottlenecks.
"""

from app.monitoring.tracing.tracer import TracingService

__all__ = ["TracingService"]
