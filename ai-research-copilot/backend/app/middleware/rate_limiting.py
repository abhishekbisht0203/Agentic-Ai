"""
Rate limiting middleware.

Provides request rate limiting using Redis.
"""

import time
from typing import Any

import redis.asyncio as redis
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.config import settings


class RateLimitMiddleware:
    """
    Pure ASGI middleware for rate limiting requests.

    Uses Redis to track request counts per client IP.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self._redis_client: redis.Redis | None = None

    async def close(self) -> None:
        """Close Redis connection gracefully."""
        if self._redis_client is not None:
            try:
                await self._redis_client.close()
            except Exception:
                pass
            self._redis_client = None

    async def _get_redis(self) -> redis.Redis | None:
        """Get or create Redis client. Returns None if connection fails."""
        if self._redis_client is None:
            try:
                self._redis_client = redis.from_url(
                    settings.redis.redis_url,
                    decode_responses=True,
                    socket_timeout=2,
                    socket_connect_timeout=2,
                )
            except Exception:
                return None
        return self._redis_client

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        client = scope.get("client")
        client_ip = client[0] if client else "unknown"

        key = f"rate_limit:{client_ip}:{int(time.time() // settings.rate_limit_period)}"

        redis_client = await self._get_redis()
        current = 0
        if redis_client is not None:
            try:
                current = await redis_client.incr(key)
                if current == 1:
                    await redis_client.expire(key, settings.rate_limit_period)

                if current > settings.rate_limit_requests:
                    import json
                    response_body = json.dumps({"error": "Rate limit exceeded"}).encode()
                    await send({
                        "type": "http.response.start",
                        "status": 429,
                        "headers": [
                            [b"content-type", b"application/json"],
                            [b"content-length", str(len(response_body)).encode()],
                        ],
                    })
                    await send({
                        "type": "http.response.body",
                        "body": response_body,
                    })
                    return
            except Exception:
                pass

        response_headers: list[list[bytes]] = []
        status_code = 500

        async def send_wrapper(message: dict[str, Any]) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 500)
                headers = list(message.get("headers", []))
                headers.append([b"X-RateLimit-Limit", str(settings.rate_limit_requests).encode()])
                headers.append([b"X-RateLimit-Remaining", str(max(0, settings.rate_limit_requests - current)).encode()])
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_wrapper)
