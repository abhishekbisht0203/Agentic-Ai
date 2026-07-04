"""
Request logging middleware.

Logs all incoming requests with structured data.
"""

from typing import Any

import structlog
from starlette.types import ASGIApp, Receive, Scope, Send

logger = structlog.get_logger()


class LoggingMiddleware:
    """
    Pure ASGI middleware for logging HTTP requests and responses.

    Provides structured logging with request ID tracking.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope["method"]
        path = scope["path"]
        query = scope.get("query_string", b"").decode()
        client = scope.get("client")
        client_host = client[0] if client else None

        logger.info(
            "Incoming request",
            method=method,
            path=path,
            query=query,
            client=client_host,
        )

        status_code = 500

        async def send_wrapper(message: dict[str, Any]) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 500)
            await send(message)

        await self.app(scope, receive, send_wrapper)

        logger.info(
            "Outgoing response",
            method=method,
            path=path,
            status_code=status_code,
        )
