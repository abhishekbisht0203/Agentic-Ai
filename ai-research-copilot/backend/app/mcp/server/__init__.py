"""
MCP Server package.

Exposes registered tools via the Model Context Protocol,
handling request routing, tool listing, and invocation.
"""

from app.mcp.server.mcp_server import MCPServer

__all__ = ["MCPServer"]
