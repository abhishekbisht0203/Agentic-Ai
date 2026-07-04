"""
Security headers middleware.

Adds security-related HTTP headers to all responses.
"""

from starlette.types import ASGIApp, Receive, Scope, Send


class SecurityHeadersMiddleware:
    """Pure ASGI middleware that adds security headers to responses."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message: dict) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))

                security_headers = [
                    [b"X-Content-Type-Options", b"nosniff"],
                    [b"X-Frame-Options", b"DENY"],
                    [b"X-XSS-Protection", b"1; mode=block"],
                    [b"Referrer-Policy", b"strict-origin-when-cross-origin"],
                    [b"Permissions-Policy", b"camera=(), microphone=(), geolocation=()"],
                    [b"Strict-Transport-Security", b"max-age=31536000; includeSubDomains"],
                ]

                existing_keys = {h[0] for h in headers}
                for header in security_headers:
                    if header[0] not in existing_keys:
                        headers.append(header)

                message["headers"] = headers

            await send(message)

        await self.app(scope, receive, send_wrapper)
