"""
Prometheus metrics collector implementation.

Provides comprehensive metrics collection for HTTP requests, LLM usage,
document processing, agent executions, and system information using
the prometheus_client library.
"""

import logging
import platform
import sys
from typing import Any

import psutil
from prometheus_client import (
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    Info,
    generate_latest,
)

logger = logging.getLogger(__name__)

REGISTRY = CollectorRegistry(auto_describe=True)


class MetricsCollector:
    """Collect and expose Prometheus metrics.

    Provides methods for recording HTTP requests, LLM API calls,
    document processing, agent executions, and generating Prometheus
    metrics in text format.

    Attributes:
        http_requests_total: Counter for total HTTP requests.
        http_request_duration_seconds: Histogram for HTTP request durations.
        active_connections: Gauge for active connections.
        llm_requests_total: Counter for total LLM requests.
        llm_token_usage: Counter for total LLM tokens used.
        documents_processed_total: Counter for total documents processed.
        agent_executions_total: Counter for total agent executions.
        system_info: Info metric for system information.
    """

    def __init__(self) -> None:
        """Initialize MetricsCollector with all metric definitions."""
        logger.debug("Initializing MetricsCollector")
        self.http_requests_total = Counter(
            "http_requests_total",
            "Total HTTP requests",
            ["method", "endpoint", "status"],
            registry=REGISTRY,
        )
        self.http_request_duration_seconds = Histogram(
            "http_request_duration_seconds",
            "HTTP request duration in seconds",
            ["method", "endpoint"],
            buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
            registry=REGISTRY,
        )
        self.active_connections = Gauge(
            "active_connections",
            "Number of active connections",
            registry=REGISTRY,
        )
        self.llm_requests_total = Counter(
            "llm_requests_total",
            "Total LLM requests",
            ["provider", "model", "status"],
            registry=REGISTRY,
        )
        self.llm_token_usage = Counter(
            "llm_token_usage_total",
            "Total LLM tokens used",
            ["provider", "model", "type"],
            registry=REGISTRY,
        )
        self.documents_processed_total = Counter(
            "documents_processed_total",
            "Total documents processed",
            ["status"],
            registry=REGISTRY,
        )
        self.agent_executions_total = Counter(
            "agent_executions_total",
            "Total agent executions",
            ["agent_type", "status"],
            registry=REGISTRY,
        )
        self.system_info = Info(
            "system",
            "System information",
            registry=REGISTRY,
        )

        self._collect_system_info()
        logger.info("MetricsCollector initialized successfully")

    def _collect_system_info(self) -> None:
        """Collect and store system information."""
        try:
            info: dict[str, str] = {
                "python_version": sys.version,
                "platform": platform.platform(),
                "processor": platform.processor() or "unknown",
                "hostname": platform.node(),
                "cpu_count": str(psutil.cpu_count(logical=True) or 0),
                "memory_total_gb": f"{psutil.virtual_memory().total / (1024**3):.2f}",
            }
            self.system_info.info(info)
            logger.debug("System info collected: %s", info)
        except Exception as e:
            logger.warning("Failed to collect system info: %s", str(e))
            self.system_info.info({"error": "Failed to collect system info"})

    def record_request(
        self, method: str, endpoint: str, status: str, duration: float
    ) -> None:
        """Record an HTTP request.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.).
            endpoint: Request endpoint path.
            status: Response status code (as string, e.g., "200", "404").
            duration: Request duration in seconds.
        """
        try:
            normalized_endpoint = self._normalize_endpoint(endpoint)
            self.http_requests_total.labels(
                method=method.upper(),
                endpoint=normalized_endpoint,
                status=status,
            ).inc()
            self.http_request_duration_seconds.labels(
                method=method.upper(),
                endpoint=normalized_endpoint,
            ).observe(duration)
            logger.debug(
                "Recorded request: %s %s %s (%.3fs)",
                method,
                normalized_endpoint,
                status,
                duration,
            )
        except Exception as e:
            logger.error("Failed to record request metric: %s", str(e))

    def record_llm_request(
        self,
        provider: str,
        model: str,
        status: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
    ) -> None:
        """Record an LLM API request.

        Args:
            provider: LLM provider name (e.g., "openai", "anthropic").
            model: Model identifier (e.g., "gpt-4", "claude-3").
            status: Request status ("success" or "error").
            prompt_tokens: Number of prompt tokens used.
            completion_tokens: Number of completion tokens generated.
        """
        try:
            self.llm_requests_total.labels(
                provider=provider,
                model=model,
                status=status,
            ).inc()

            if prompt_tokens > 0:
                self.llm_token_usage.labels(
                    provider=provider,
                    model=model,
                    type="prompt",
                ).inc(prompt_tokens)

            if completion_tokens > 0:
                self.llm_token_usage.labels(
                    provider=provider,
                    model=model,
                    type="completion",
                ).inc(completion_tokens)

            logger.debug(
                "Recorded LLM request: %s/%s %s (prompt=%d, completion=%d)",
                provider,
                model,
                status,
                prompt_tokens,
                completion_tokens,
            )
        except Exception as e:
            logger.error("Failed to record LLM request metric: %s", str(e))

    def record_document_processing(self, status: str) -> None:
        """Record a document processing event.

        Args:
            status: Processing status ("success" or "error").
        """
        try:
            self.documents_processed_total.labels(status=status).inc()
            logger.debug("Recorded document processing: %s", status)
        except Exception as e:
            logger.error(
                "Failed to record document processing metric: %s", str(e)
            )

    def record_agent_execution(self, agent_type: str, status: str) -> None:
        """Record an agent execution event.

        Args:
            agent_type: Type of agent (e.g., "research", "code_assistant").
            status: Execution status ("success" or "error").
        """
        try:
            self.agent_executions_total.labels(
                agent_type=agent_type,
                status=status,
            ).inc()
            logger.debug(
                "Recorded agent execution: %s %s", agent_type, status
            )
        except Exception as e:
            logger.error("Failed to record agent execution metric: %s", str(e))

    def increment_active_connections(self) -> None:
        """Increment the active connections counter."""
        try:
            self.active_connections.inc()
        except Exception as e:
            logger.error("Failed to increment active connections: %s", str(e))

    def decrement_active_connections(self) -> None:
        """Decrement the active connections counter."""
        try:
            self.active_connections.dec()
        except Exception as e:
            logger.error("Failed to decrement active connections: %s", str(e))

    def get_metrics(self) -> bytes:
        """Generate Prometheus metrics in text format.

        Returns:
            UTF-8 encoded bytes containing all metrics in Prometheus text format.
        """
        try:
            return generate_latest(REGISTRY)
        except Exception as e:
            logger.error("Failed to generate metrics: %s", str(e))
            return b""

    def get_metrics_dict(self) -> dict[str, Any]:
        """Get metrics as a dictionary.

        Returns:
            Dictionary containing metric names and their current values.
        """
        try:
            metrics_output = generate_latest(REGISTRY).decode("utf-8")
            metrics_dict: dict[str, Any] = {}

            for line in metrics_output.split("\n"):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    name, value = line.split("=", 1)
                    try:
                        metrics_dict[name] = float(value)
                    except ValueError:
                        metrics_dict[name] = value

            return metrics_dict
        except Exception as e:
            logger.error("Failed to get metrics dict: %s", str(e))
            return {}

    @staticmethod
    def _normalize_endpoint(endpoint: str) -> str:
        """Normalize endpoint path to reduce cardinality.

        Converts dynamic path segments to placeholders to prevent
        high-cardinality metrics.

        Args:
            endpoint: Original endpoint path.

        Returns:
            Normalized endpoint path.
        """
        import re

        normalized = re.sub(
            r"/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            "/{uuid}",
            endpoint,
            flags=re.IGNORECASE,
        )
        normalized = re.sub(r"/\d+", "/{id}", normalized)
        return normalized


metrics = MetricsCollector()
