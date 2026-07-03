"""
Request logging middleware.

Logs all incoming requests with structured data.
"""

from typing import Any

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger()


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging HTTP requests and responses.

    Provides structured logging with request ID tracking.
    """

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        """
        Process request and log it.

        Args:
            request: Incoming HTTP request.
            call_next: Next middleware/handler in chain.

        Returns:
            HTTP response.
        """
        # Log incoming request
        logger.info(
            "Incoming request",
            method=request.method,
            path=request.url.path,
            query=request.url.query,
            client=request.client.host if request.client else None,
        )

        # Call next handler
        response = await call_next(request)

        # Log response
        logger.info(
            "Outgoing response",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
        )

        return response
