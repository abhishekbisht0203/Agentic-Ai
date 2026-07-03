"""
MCP (Model Context Protocol) package.

Provides tool registry, server, client, and executor components
for exposing and consuming tools via the MCP protocol.
"""

from app.mcp.registry.tool_registry import MCPTool, ToolRegistry
from app.mcp.server.mcp_server import MCPServer
from app.mcp.client.mcp_client import MCPClient
from app.mcp.executors.tool_executor import ToolExecutor
from app.mcp.tools.builtin_tools import register_built_in_tools

__all__ = [
    "MCPTool",
    "ToolRegistry",
    "MCPServer",
    "MCPClient",
    "ToolExecutor",
    "register_built_in_tools",
]
