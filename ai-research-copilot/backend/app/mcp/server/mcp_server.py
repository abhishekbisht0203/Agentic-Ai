"""
MCP Server implementation.

Handles incoming MCP protocol requests, dispatches tool calls,
and returns structured responses conforming to the MCP specification.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from app.mcp.registry.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)

# MCP protocol version supported by this implementation
MCP_PROTOCOL_VERSION = "2024-11-05"

# Standard JSON-RPC error codes
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603


class MCPServer:
    """MCP server that exposes tools via the Model Context Protocol.

    Implements the JSON-RPC based MCP transport, handling:
    - ``initialize`` handshake
    - ``tools/list`` discovery
    - ``tools/call`` execution
    - Ping and error responses

    Args:
        registry: The ToolRegistry containing available tools.
    """

    def __init__(self, registry: ToolRegistry) -> None:
        self.registry = registry
        self._server_info = {
            "name": "ai-research-copilot-mcp",
            "version": "1.0.0",
        }
        self._capabilities = {
            "tools": {"listChanged": False},
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def handle_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """Process a single MCP/JSON-RPC request and return a response.

        Args:
            request: A JSON-RPC style request dictionary.

        Returns:
            A JSON-RPC style response dictionary.
        """
        request_id = request.get("id")
        method = request.get("method", "")
        params = request.get("params", {})

        logger.debug("MCP request: method=%s id=%s", method, request_id)

        try:
            if method == "initialize":
                result = self._handle_initialize(params)
            elif method == "notifications/initialized":
                return self._make_response(request_id, result=None)
            elif method == "tools/list":
                result = self._handle_tools_list(params)
            elif method == "tools/call":
                result = await self._handle_tools_call(params)
            elif method == "ping":
                result = {}
            else:
                return self._make_error(
                    request_id, METHOD_NOT_FOUND, f"Method not found: {method}"
                )
        except ValueError as exc:
            return self._make_error(request_id, INVALID_PARAMS, str(exc))
        except Exception as exc:
            logger.exception("MCP server error processing %s", method)
            return self._make_error(request_id, INTERNAL_ERROR, str(exc))

        return self._make_response(request_id, result=result)

    def get_tool_definitions(self) -> list[dict[str, Any]]:
        """Return MCP-compatible tool definitions for all registered tools.

        Returns:
            A list of tool definition dictionaries.
        """
        return self.registry.list_tools()

    # ------------------------------------------------------------------
    # Internal request handlers
    # ------------------------------------------------------------------

    def _handle_initialize(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle the ``initialize`` handshake.

        Args:
            params: Client-supplied initialization parameters.

        Returns:
            Server capabilities and protocol version information.
        """
        client_info = params.get("clientInfo", {})
        logger.info(
            "MCP client connected: %s (v%s)",
            client_info.get("name", "unknown"),
            client_info.get("version", "unknown"),
        )
        return {
            "protocolVersion": MCP_PROTOCOL_VERSION,
            "capabilities": self._capabilities,
            "serverInfo": self._server_info,
        }

    def _handle_tools_list(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle the ``tools/list`` request.

        Args:
            params: Optional filtering parameters (e.g. cursor).

        Returns:
            A dictionary containing the list of available tools.
        """
        category = params.get("category")
        tools = self.registry.list_tools(category=category)
        logger.debug("Listed %d MCP tools", len(tools))
        return {"tools": tools}

    async def _handle_tools_call(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle the ``tools/call`` request.

        Args:
            params: Must include ``name`` and optionally ``arguments``.

        Returns:
            A dictionary with ``content`` containing the tool result,
            or ``isError`` set to true on failure.

        Raises:
            ValueError: If the ``name`` parameter is missing.
        """
        tool_name = params.get("name")
        if not tool_name:
            raise ValueError("Missing required parameter: name")

        arguments = params.get("arguments", {})

        tool = self.registry.get(tool_name)
        if not tool:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Tool not found: {tool_name}",
                    }
                ],
                "isError": True,
            }

        try:
            result = await self.registry.execute(tool_name, **arguments)
            content = self._serialize_result(result)
            return {"content": content, "isError": False}
        except Exception as exc:
            logger.exception("MCP tool call failed: %s", tool_name)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Tool execution failed: {exc}",
                    }
                ],
                "isError": True,
            }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _serialize_result(result: Any) -> list[dict[str, Any]]:
        """Convert a tool result into MCP content blocks.

        Args:
            result: The raw result from the tool handler.

        Returns:
            A list of MCP content block dictionaries.
        """
        if isinstance(result, str):
            return [{"type": "text", "text": result}]
        if isinstance(result, dict):
            return [{"type": "text", "text": json.dumps(result, default=str)}]
        if isinstance(result, (list, tuple)):
            return [{"type": "text", "text": json.dumps(list(result), default=str)}]
        return [{"type": "text", "text": json.dumps(result, default=str)}]

    @staticmethod
    def _make_response(
        request_id: str | int | None, result: Any
    ) -> dict[str, Any]:
        """Build a JSON-RPC success response.

        Args:
            request_id: The original request identifier.
            result: The result payload.

        Returns:
            A JSON-RPC response dictionary.
        """
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result,
        }

    @staticmethod
    def _make_error(
        request_id: str | int | None,
        code: int,
        message: str,
        data: Any = None,
    ) -> dict[str, Any]:
        """Build a JSON-RPC error response.

        Args:
            request_id: The original request identifier.
            code: The JSON-RPC error code.
            message: Human-readable error description.
            data: Optional additional error data.

        Returns:
            A JSON-RPC error response dictionary.
        """
        error: dict[str, Any] = {"code": code, "message": message}
        if data is not None:
            error["data"] = data
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": error,
        }
