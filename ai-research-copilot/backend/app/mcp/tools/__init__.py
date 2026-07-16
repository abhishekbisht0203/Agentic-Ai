"""
MCP Tools package.

Registers built-in and coding tools that ship with the application.
"""

from app.mcp.tools.builtin_tools import register_built_in_tools
from app.mcp.tools.coding_tools import register_coding_tools

__all__ = ["register_built_in_tools", "register_coding_tools"]
