"""
Prometheus metrics collection module.

Provides a MetricsCollector class for tracking HTTP requests, LLM usage,
document processing, agent executions, and system information.
"""

from app.monitoring.metrics.prometheus import MetricsCollector, metrics

__all__ = ["MetricsCollector", "metrics"]
