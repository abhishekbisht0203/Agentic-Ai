"""
MCP Server backward-compatibility shim.

Re-exports ``MCPServer`` from the package implementation so that
existing imports via ``app.mcp.server`` continue to work.
"""

from app.mcp.server.mcp_server import MCPServer

__all__ = ["MCPServer"]
