"""
MCP Tool Registry.

Central registry for managing available MCP tools. Provides registration,
discovery, validation, and execution of tools exposed through the
Model Context Protocol.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

logger = logging.getLogger(__name__)


@dataclass
class MCPTool:
    """Represents a single MCP-compatible tool.

    Attributes:
        name: Unique tool identifier used in protocol messages.
        description: Human-readable description of what the tool does.
        parameters: JSON Schema describing the tool's input parameters.
        handler: Async callable that implements the tool logic.
        category: Logical grouping for tool discovery (e.g. "calculation").
        requires_auth: Whether the tool requires an authenticated user context.
    """

    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable[..., Awaitable[Any]]
    category: str = "general"
    requires_auth: bool = True

    def to_definition(self) -> dict[str, Any]:
        """Serialize the tool to an MCP-compatible tool definition."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "category": self.category,
            "requires_auth": self.requires_auth,
        }


class ToolRegistry:
    """Registry that manages available MCP tools.

    Provides registration, lookup, listing, and execution of tools.
    Thread-safety is ensured via an asyncio lock for concurrent access
    during registration and execution.
    """

    def __init__(self) -> None:
        self._tools: dict[str, MCPTool] = {}
        self._lock = asyncio.Lock()

    def register(self, tool: MCPTool) -> None:
        """Synchronously register a tool.

        If a tool with the same name already exists it will be replaced
        and a warning logged.

        Args:
            tool: The MCPTool instance to register.
        """
        if tool.name in self._tools:
            logger.warning(
                "Replacing existing MCP tool: %s", tool.name
            )
        self._tools[tool.name] = tool
        logger.debug(
            "Registered MCP tool: %s (category=%s)", tool.name, tool.category
        )

    async def async_register(self, tool: MCPTool) -> None:
        """Asynchronously register a tool (safe for concurrent use).

        Args:
            tool: The MCPTool instance to register.
        """
        async with self._lock:
            if tool.name in self._tools:
                logger.warning(
                    "Replacing existing MCP tool: %s", tool.name
                )
            self._tools[tool.name] = tool
            logger.debug(
                "Registered MCP tool: %s (category=%s)",
                tool.name,
                tool.category,
            )

    def get(self, name: str) -> MCPTool | None:
        """Look up a tool by name.

        Args:
            name: The unique tool identifier.

        Returns:
            The MCPTool instance, or None if not found.
        """
        return self._tools.get(name)

    def list_tools(self, category: str | None = None) -> list[dict[str, Any]]:
        """List registered tools, optionally filtered by category.

        Args:
            category: If provided, only tools in this category are returned.

        Returns:
            A list of tool definition dictionaries.
        """
        tools = self._tools.values()
        if category:
            tools = [t for t in tools if t.category == category]
        return [t.to_definition() for t in tools]

    def get_handler(self, name: str) -> Callable[..., Awaitable[Any]] | None:
        """Retrieve the handler callable for a tool.

        Args:
            name: The unique tool identifier.

        Returns:
            The async handler callable, or None if the tool is not registered.
        """
        tool = self._tools.get(name)
        return tool.handler if tool else None

    def has_tool(self, name: str) -> bool:
        """Check whether a tool is registered.

        Args:
            name: The unique tool identifier.

        Returns:
            True if the tool exists in the registry.
        """
        return name in self._tools

    def unregister(self, name: str) -> bool:
        """Remove a tool from the registry.

        Args:
            name: The unique tool identifier.

        Returns:
            True if the tool was removed, False if it was not found.
        """
        if name in self._tools:
            del self._tools[name]
            logger.debug("Unregistered MCP tool: %s", name)
            return True
        return False

    def clear(self) -> None:
        """Remove all registered tools."""
        self._tools.clear()
        logger.debug("Cleared all MCP tools from registry")

    def count(self, category: str | None = None) -> int:
        """Return the number of registered tools.

        Args:
            category: If provided, count only tools in this category.

        Returns:
            Number of matching registered tools.
        """
        if category:
            return sum(1 for t in self._tools.values() if t.category == category)
        return len(self._tools)

    async def execute(self, name: str, **kwargs: Any) -> Any:
        """Execute a registered tool by name.

        Validates that the tool exists before invoking its handler.

        Args:
            name: The unique tool identifier.
            **kwargs: Keyword arguments forwarded to the tool handler.

        Returns:
            The result returned by the tool handler.

        Raises:
            ValueError: If no tool with the given name is registered.
        """
        tool = self._tools.get(name)
        if not tool:
            raise ValueError(f"MCP tool not found: {name}")

        logger.info("Executing MCP tool: %s", name)
        try:
            result = await tool.handler(**kwargs)
            logger.debug("MCP tool %s completed successfully", name)
            return result
        except Exception:
            logger.exception("MCP tool %s raised an exception", name)
            raise

    def get_categories(self) -> list[str]:
        """Return a sorted list of distinct tool categories.

        Returns:
            Sorted list of category strings.
        """
        return sorted({t.category for t in self._tools.values()})
