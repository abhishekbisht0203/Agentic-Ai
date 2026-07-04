"""
AI Research Copilot - Main Application Entry Point

FastAPI application factory with complete middleware, routing, and configuration.
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import settings
from app.core.exceptions import AIRCError
from app.database.session import close_db, init_db
from app.middleware.logging import LoggingMiddleware
from app.middleware.rate_limiting import RateLimitMiddleware
from app.routers import api_router

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

_start_time: float = 0.0


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    """Application lifespan manager for startup and shutdown."""
    global _start_time
    logger.info("Starting AI Research Copilot application...")
    _start_time = time.time()

    try:
        await init_db()
        logger.info("Database initialized")
    except Exception as exc:
        logger.warning("Database init failed (non-fatal): %s", exc)

    try:
        from app.cache.redis.cache import RedisCache
        await RedisCache.initialize()
        logger.info("Redis initialized")
    except Exception as exc:
        logger.warning("Redis init failed (non-fatal): %s", exc)

    logger.info("Application startup complete")

    yield

    logger.info("Shutting down AI Research Copilot application...")

    try:
        await close_db()
    except Exception:
        pass

    try:
        from app.cache.redis.cache import RedisCache
        await RedisCache.close()
    except Exception:
        pass

    logger.info("Application shutdown complete")


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.name,
        description="Enterprise Agentic AI Research Copilot",
        version=settings.version,
        debug=settings.debug,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    if not settings.debug:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*"],
        )

    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

    app.include_router(api_router, prefix="/api/v1")

    register_exception_handlers(app)

    @app.get("/health")
    async def health_check() -> dict[str, str]:
        """Health check endpoint for load balancers."""
        return {"status": "healthy", "version": settings.version}

    @app.get("/health/detailed")
    async def health_check_detailed() -> dict[str, Any]:
        """Detailed health check with service statuses."""
        db_status = "connected"
        redis_status = "connected"
        qdrant_status = "connected"

        try:
            from app.database.session import engine
            async with engine.connect() as conn:
                await conn.execute(
                    __import__("sqlalchemy").text("SELECT 1")
                )
        except Exception:
            db_status = "disconnected"

        try:
            from app.cache.redis.cache import RedisCache
            if not RedisCache.is_connected:
                redis_status = "disconnected"
        except Exception:
            redis_status = "disconnected"

        try:
            from qdrant_client import QdrantClient
            client = QdrantClient(
                host=settings.qdrant.host,
                port=settings.qdrant.port,
            )
            client.get_collections()
        except Exception:
            qdrant_status = "disconnected"

        uptime = time.time() - _start_time if _start_time else 0
        overall = "healthy" if db_status == "connected" else "degraded"

        return {
            "status": overall,
            "version": settings.version,
            "database": db_status,
            "redis": redis_status,
            "qdrant": qdrant_status,
            "uptime_seconds": round(uptime, 2),
        }

    @app.get("/metrics")
    async def metrics() -> Response:
        """Prometheus metrics endpoint."""
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST,
        )

    return app


def register_exception_handlers(app: FastAPI) -> None:
    """Register custom exception handlers."""

    @app.exception_handler(AIRCError)
    async def airc_error_handler(request: Request, exc: AIRCError) -> JSONResponse:
        """Handle custom AIRC errors."""
        logger.error("AIRC Error: %s - %s", exc.code, exc.message, extra=exc.details)
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                }
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle unexpected errors."""
        logger.exception("Unexpected error occurred")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                }
            },
        )


app = create_application()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )