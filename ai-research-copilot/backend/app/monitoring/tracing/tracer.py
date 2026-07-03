"""
OpenTelemetry tracing service implementation.

Provides distributed tracing capabilities using OpenTelemetry for
tracking request flows across services and identifying performance bottlenecks.
"""

import logging
from contextlib import contextmanager
from typing import Any, Generator

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Span, StatusCode

logger = logging.getLogger(__name__)


class TracingService:
    """OpenTelemetry tracing service.

    Manages the lifecycle of OpenTelemetry tracing including initialization,
    provider configuration, and span creation for operation tracing.

    Attributes:
        provider: The OpenTelemetry TracerProvider instance.
        tracer: The OpenTelemetry Tracer instance.
    """

    def __init__(self, service_name: str = "ai-research-copilot") -> None:
        """Initialize TracingService.

        Args:
            service_name: Name of the service for trace identification.
        """
        self.service_name = service_name
        self.resource = Resource.create({SERVICE_NAME: service_name})
        self.provider = TracerProvider(resource=self.resource)
        trace.set_tracer_provider(self.provider)
        self.tracer = trace.get_tracer(service_name)
        self._initialized = False
        logger.info("TracingService created for service: %s", service_name)

    def initialize(self, endpoint: str | None = None) -> None:
        """Initialize tracing with optional OTLP endpoint.

        Configures the tracing provider with console and optional OTLP export.

        Args:
            endpoint: Optional OTLP collector endpoint URL. If None, only
                     console export is used.
        """
        if self._initialized:
            logger.warning("Tracing already initialized, skipping")
            return

        try:
            from opentelemetry.sdk.trace.export import ConsoleSpanExporter

            console_exporter = ConsoleSpanExporter()
            console_processor = BatchSpanProcessor(console_exporter)
            self.provider.add_span_processor(console_processor)
            logger.info("Console span exporter added")

            if endpoint:
                try:
                    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                        OTLPSpanExporter,
                    )

                    otlp_exporter = OTLPSpanExporter(endpoint=endpoint)
                    otlp_processor = BatchSpanProcessor(otlp_exporter)
                    self.provider.add_span_processor(otlp_processor)
                    logger.info("OTLP span exporter added with endpoint: %s", endpoint)
                except ImportError:
                    logger.warning(
                        "OTLP exporter not available. Install opentelemetry-exporter-otlp-proto-grpc"
                    )
                except Exception as e:
                    logger.error("Failed to configure OTLP exporter: %s", str(e))

            self._initialized = True
            logger.info("Tracing initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize tracing: %s", str(e))
            raise

    def instrument_fastapi(self, app: Any) -> None:
        """Instrument FastAPI with OpenTelemetry.

        Adds automatic tracing middleware to a FastAPI application.

        Args:
            app: The FastAPI application instance to instrument.
        """
        try:
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

            FastAPIInstrumentor.instrument_app(app)
            logger.info("FastAPI application instrumented with OpenTelemetry")
        except ImportError:
            logger.warning(
                "FastAPI instrumentation not available. "
                "Install opentelemetry-instrumentation-fastapi"
            )
        except Exception as e:
            logger.error("Failed to instrument FastAPI: %s", str(e))
            raise

    @contextmanager
    def trace_operation(
        self,
        name: str,
        attributes: dict[str, Any] | None = None,
    ) -> Generator[Span, None, None]:
        """Context manager for tracing an operation.

        Creates a new span for the duration of the context manager and
        records any exceptions that occur.

        Args:
            name: Name of the operation to trace.
            attributes: Optional dictionary of attributes to attach to the span.

        Yields:
            The active OpenTelemetry Span instance.

        Example:
            >>> with tracer.trace_operation("process_data", {"batch_size": 100}):
            ...     process_data()
        """
        span = self.tracer.start_span(name)
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, str(value))

        try:
            yield span
            span.set_status(StatusCode.OK)
        except Exception as e:
            span.set_status(StatusCode.ERROR, str(e))
            span.record_exception(e)
            logger.error("Traced operation '%s' failed: %s", name, str(e))
            raise
        finally:
            span.end()

    def get_current_span(self) -> Span | None:
        """Get the current active span.

        Returns:
            The current active span, or None if no span is active.
        """
        return trace.get_current_span()

    def add_event(
        self, name: str, attributes: dict[str, Any] | None = None
    ) -> None:
        """Add an event to the current active span.

        Args:
            name: Name of the event.
            attributes: Optional dictionary of attributes for the event.
        """
        current_span = trace.get_current_span()
        if current_span and current_span.is_recording():
            attrs = {k: str(v) for k, v in (attributes or {}).items()}
            current_span.add_event(name, attrs)

    def shutdown(self) -> None:
        """Shutdown the tracing provider and flush pending spans."""
        try:
            self.provider.shutdown()
            logger.info("Tracing provider shutdown successfully")
        except Exception as e:
            logger.error("Failed to shutdown tracing provider: %s", str(e))
