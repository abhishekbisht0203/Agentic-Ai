"""
MCP Client implementation.

HTTP-based client for calling external MCP servers. Supports tool
discovery, tool invocation, and connection lifecycle management
via the ``httpx`` async HTTP library.
"""

import json
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class MCPClientError(Exception):
    """Raised when an MCP client operation fails."""

    def __init__(self, message: str, status_code: int | None = None, detail: Any = None) -> None:
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(message)


class MCPClient:
    """Async client for communicating with an external MCP server.

    Args:
        server_url: Base URL of the remote MCP server (e.g. ``http://localhost:8080/mcp``).
        timeout: Default request timeout in seconds.
    """

    def __init__(self, server_url: str, timeout: int = 30) -> None:
        self.server_url = server_url.rstrip("/")
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None
        self._request_id = 0
        self._initialized = False

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    async def _get_client(self) -> httpx.AsyncClient:
        """Lazily create and return the underlying HTTP client.

        Returns:
            An initialised ``httpx.AsyncClient`` instance.
        """
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.server_url,
                timeout=httpx.Timeout(self.timeout),
                headers={"Content-Type": "application/json"},
            )
        return self._client

    async def initialize(self) -> dict[str, Any]:
        """Perform the MCP ``initialize`` handshake with the remote server.

        Returns:
            Server capabilities returned during initialization.

        Raises:
            MCPClientError: If the handshake fails.
        """
        response = await self._send_request(
            "initialize",
            {
                "clientInfo": {
                    "name": "ai-research-copilot-client",
                    "version": "1.0.0",
                },
                "capabilities": {},
            },
        )
        self._initialized = True
        logger.info(
            "MCP client initialized with server: %s",
            response.get("serverInfo", {}).get("name", "unknown"),
        )
        return response

    async def close(self) -> None:
        """Close the underlying HTTP client and release resources."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
            self._initialized = False
            logger.debug("MCP client connection closed")

    # ------------------------------------------------------------------
    # Tool operations
    # ------------------------------------------------------------------

    async def list_tools(self, category: str | None = None) -> list[dict[str, Any]]:
        """Discover tools available on the remote MCP server.

        Args:
            category: Optional category to filter the tool list.

        Returns:
            A list of tool definition dictionaries.
        """
        params: dict[str, Any] = {}
        if category:
            params["category"] = category

        response = await self._send_request("tools/list", params)
        return response.get("tools", [])

    async def call_tool(
        self, tool_name: str, arguments: dict[str, Any] | None = None
    ) -> Any:
        """Invoke a tool on the remote MCP server.

        Args:
            tool_name: The name of the tool to invoke.
            arguments: Optional keyword arguments for the tool.

        Returns:
            The deserialized tool result.

        Raises:
            MCPClientError: If the remote call reports an error.
        """
        params: dict[str, Any] = {"name": tool_name}
        if arguments:
            params["arguments"] = arguments

        response = await self._send_request("tools/call", params)

        if response.get("isError"):
            error_text = "Unknown error"
            content = response.get("content", [])
            if content and isinstance(content, list):
                error_text = content[0].get("text", error_text)
            raise MCPClientError(
                message=f"Remote tool '{tool_name}' failed: {error_text}",
                detail=response,
            )

        content = response.get("content", [])
        if content and isinstance(content, list):
            first = content[0]
            text = first.get("text", "")
            try:
                return json.loads(text)
            except (json.JSONDecodeError, TypeError):
                return text
        return content

    async def ping(self) -> bool:
        """Ping the remote MCP server to check connectivity.

        Returns:
            True if the server responded successfully.
        """
        try:
            await self._send_request("ping", {})
            return True
        except MCPClientError:
            return False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _next_request_id(self) -> int:
        """Generate the next unique request ID."""
        self._request_id += 1
        return self._request_id

    async def _send_request(
        self, method: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        """Send a JSON-RPC request to the remote MCP server.

        Args:
            method: The MCP method name.
            params: Method parameters.

        Returns:
            The ``result`` field from the JSON-RPC response.

        Raises:
            MCPClientError: On HTTP or protocol-level errors.
        """
        client = await self._get_client()
        request_id = self._next_request_id()

        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params,
        }

        try:
            http_response = await client.post("/", json=payload)
        except httpx.TimeoutException as exc:
            raise MCPClientError(
                message=f"Request timed out: {method}",
                status_code=None,
                detail=str(exc),
            ) from exc
        except httpx.RequestError as exc:
            raise MCPClientError(
                message=f"Connection error: {method}",
                status_code=None,
                detail=str(exc),
            ) from exc

        if http_response.status_code != 200:
            raise MCPClientError(
                message=f"HTTP {http_response.status_code} for {method}",
                status_code=http_response.status_code,
                detail=http_response.text,
            )

        try:
            body = http_response.json()
        except json.JSONDecodeError as exc:
            raise MCPClientError(
                message="Invalid JSON response from MCP server",
                status_code=http_response.status_code,
            ) from exc

        if "error" in body:
            error = body["error"]
            raise MCPClientError(
                message=error.get("message", "Unknown RPC error"),
                status_code=http_response.status_code,
                detail=error,
            )

        return body.get("result", {})

    async def __aenter__(self) -> "MCPClient":
        """Support ``async with`` context manager."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Support ``async with`` context manager."""
        await self.close()
