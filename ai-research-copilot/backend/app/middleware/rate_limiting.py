"""
Rate limiting middleware.

Provides request rate limiting using Redis.
"""

import time
from typing import Any

import redis.asyncio as redis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware for rate limiting requests.

    Uses Redis to track request counts per client IP.
    """

    def __init__(self, app: Any) -> None:
        """
        Initialize rate limiting middleware.

        Args:
            app: ASGI application.
        """
        super().__init__(app)
        self._redis_client: redis.Redis | None = None

    async def _get_redis(self) -> redis.Redis:
        """Get or create Redis client."""
        if self._redis_client is None:
            self._redis_client = redis.from_url(
                settings.redis.redis_url,
                decode_responses=True,
            )
        return self._redis_client

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        """
        Process request with rate limiting check.

        Args:
            request: Incoming HTTP request.
            call_next: Next middleware/handler in chain.

        Returns:
            HTTP response or rate limit error.
        """
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"

        # Create rate limit key
        key = f"rate_limit:{client_ip}:{int(time.time() // settings.rate_limit_period)}"

        # Check rate limit
        redis_client = await self._get_redis()
        try:
            current = await redis_client.incr(key)
            if current == 1:
                await redis_client.expire(key, settings.rate_limit_period)

            if current > settings.rate_limit_requests:
                return Response(
                    content='{"error": "Rate limit exceeded"}',
                    status_code=429,
                    media_type="application/json",
                )
        except Exception:
            # If Redis fails, allow the request
            pass

        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(settings.rate_limit_requests)
        response.headers["X-RateLimit-Remaining"] = str(max(0, settings.rate_limit_requests - current))

        return response
