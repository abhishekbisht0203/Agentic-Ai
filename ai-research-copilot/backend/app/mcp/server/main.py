"""
MCP Server - Standalone Service Entry Point

FastAPI application for running the MCP server as a separate microservice.
"""

import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from app.mcp.registry.tool_registry import ToolRegistry
from app.mcp.server.mcp_server import MCPServer
from app.mcp.tools.builtin_tools import register_built_in_tools

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global instances
_tool_registry: ToolRegistry | None = None
_mcp_server: MCPServer | None = None
_start_time: float = 0.0


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global _tool_registry, _mcp_server, _start_time

    logger.info("Starting MCP Server...")
    _start_time = time.time()

    # Initialize tool registry and register built-in tools
    _tool_registry = ToolRegistry()
    register_built_in_tools(_tool_registry)

    # Initialize MCP server
    _mcp_server = MCPServer(_tool_registry)

    logger.info(
        "MCP Server started with %d tools registered",
        _tool_registry.count(),
    )

    yield

    logger.info("Shutting down MCP Server...")


def create_mcp_app() -> FastAPI:
    """Create and configure the MCP FastAPI application."""

    app = FastAPI(
        title="AI Research Copilot - MCP Server",
        description="Model Context Protocol server for tool execution",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health_check() -> dict[str, Any]:
        """Health check endpoint."""
        uptime = time.time() - _start_time if _start_time else 0
        return {
            "status": "healthy",
            "version": "1.0.0",
            "uptime_seconds": round(uptime, 2),
            "tools_registered": _tool_registry.count() if _tool_registry else 0,
        }

    @app.get("/health/detailed")
    async def health_check_detailed() -> dict[str, Any]:
        """Detailed health check with tool information."""
        uptime = time.time() - _start_time if _start_time else 0
        return {
            "status": "healthy",
            "version": "1.0.0",
            "uptime_seconds": round(uptime, 2),
            "tools_registered": _tool_registry.count() if _tool_registry else 0,
            "tools_by_category": {
                cat: _tool_registry.count(category=cat)
                for cat in (_tool_registry.get_categories() if _tool_registry else [])
            },
            "protocol_version": "2024-11-05",
        }

    @app.post("/")
    async def handle_mcp_request(request: Request) -> JSONResponse:
        """Handle MCP JSON-RPC requests."""
        try:
            body = await request.json()

            if _mcp_server is None:
                return JSONResponse(
                    status_code=503,
                    content={
                        "jsonrpc": "2.0",
                        "id": body.get("id"),
                        "error": {"code": -32000, "message": "Server not ready"},
                    },
                )

            response = await _mcp_server.handle_request(body)
            return JSONResponse(content=response)

        except Exception as exc:
            logger.exception("Error handling MCP request")
            return JSONResponse(
                status_code=500,
                content={
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32603, "message": str(exc)},
                },
            )

    @app.get("/tools")
    async def list_tools() -> dict[str, Any]:
        """List all available MCP tools."""
        if _tool_registry is None:
            return {"tools": []}
        return {"tools": _tool_registry.list_tools()}

    @app.get("/tools/{category}")
    async def list_tools_by_category(category: str) -> dict[str, Any]:
        """List tools filtered by category."""
        if _tool_registry is None:
            return {"tools": []}
        return {"tools": _tool_registry.list_tools(category=category)}

    @app.get("/categories")
    async def list_categories() -> dict[str, Any]:
        """List all tool categories."""
        if _tool_registry is None:
            return {"categories": []}
        return {"categories": _tool_registry.get_categories()}

    return app


app = create_mcp_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.mcp.server.main:app",
        host="0.0.0.0",
        port=8100,
        workers=4,
        log_level="info",
    )
