"""
MCP Tool Executor.

Runs MCP tools with timeout enforcement, structured result packaging,
and comprehensive error handling. Wraps the ToolRegistry to provide
a safer execution layer for calling tools from workflows and agents.
"""

import asyncio
import logging
import time
from typing import Any

from app.mcp.registry.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)


class ToolExecutionError(Exception):
    """Raised when a tool execution fails after all retry attempts."""

    def __init__(self, tool_name: str, message: str, detail: Any = None) -> None:
        self.tool_name = tool_name
        self.message = message
        self.detail = detail
        super().__init__(f"Tool '{tool_name}' failed: {message}")


class ToolExecutor:
    """Executor that runs MCP tools with timeout and error handling.

    Provides a controlled execution environment for tools, enforcing
    timeouts and capturing structured execution metadata.

    Args:
        registry: The ToolRegistry containing available tools.
        timeout: Default execution timeout in seconds.
    """

    def __init__(self, registry: ToolRegistry, timeout: int = 60) -> None:
        self.registry = registry
        self.timeout = timeout

    async def execute_with_timeout(
        self,
        tool_name: str,
        timeout: int | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Execute a tool with timeout enforcement.

        Runs the named tool inside an ``asyncio.wait_for`` wrapper and
        returns a structured result dictionary containing execution metadata.

        Args:
            tool_name: Name of the tool to execute.
            timeout: Override the default timeout (seconds).
            **kwargs: Arguments forwarded to the tool handler.

        Returns:
            A dictionary with keys:
              - ``success`` (bool): Whether the execution succeeded.
              - ``tool_name`` (str): Name of the executed tool.
              - ``result`` (Any): The tool's return value on success.
              - ``error`` (str | None): Error message on failure.
              - ``duration_ms`` (int): Wall-clock execution time in ms.
              - ``timed_out`` (bool): Whether the execution was aborted due to timeout.

        Raises:
            ValueError: If the tool is not registered.
        """
        tool = self.registry.get(tool_name)
        if not tool:
            raise ValueError(f"MCP tool not found: {tool_name}")

        effective_timeout = timeout if timeout is not None else self.timeout
        start_time = time.monotonic()

        logger.info(
            "Executing MCP tool: %s (timeout=%ds)", tool_name, effective_timeout
        )

        try:
            result = await asyncio.wait_for(
                self.registry.execute(tool_name, **kwargs),
                timeout=effective_timeout,
            )
            duration_ms = int((time.monotonic() - start_time) * 1000)

            logger.info(
                "Tool %s completed in %dms", tool_name, duration_ms
            )

            return {
                "success": True,
                "tool_name": tool_name,
                "result": result,
                "error": None,
                "duration_ms": duration_ms,
                "timed_out": False,
            }

        except asyncio.TimeoutError:
            duration_ms = int((time.monotonic() - start_time) * 1000)
            logger.warning(
                "Tool %s timed out after %dms", tool_name, duration_ms
            )
            return {
                "success": False,
                "tool_name": tool_name,
                "result": None,
                "error": f"Tool execution timed out after {effective_timeout}s",
                "duration_ms": duration_ms,
                "timed_out": True,
            }

        except Exception as exc:
            duration_ms = int((time.monotonic() - start_time) * 1000)
            logger.exception("Tool %s raised an exception", tool_name)
            return {
                "success": False,
                "tool_name": tool_name,
                "result": None,
                "error": str(exc),
                "duration_ms": duration_ms,
                "timed_out": False,
            }

    async def execute_batch(
        self,
        calls: list[dict[str, Any]],
        timeout: int | None = None,
    ) -> list[dict[str, Any]]:
        """Execute multiple tool calls concurrently.

        Each entry in ``calls`` must have a ``tool_name`` key and
        optionally an ``arguments`` dict.

        Args:
            calls: List of tool call specifications.
            timeout: Timeout per individual tool call.

        Returns:
            A list of result dictionaries in the same order as the input calls.
        """
        tasks = []
        for call in calls:
            tool_name = call.get("tool_name", "")
            arguments = call.get("arguments", {})
            tasks.append(
                self.execute_with_timeout(tool_name, timeout=timeout, **arguments)
            )

        results = await asyncio.gather(*tasks, return_exceptions=True)

        processed: list[dict[str, Any]] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed.append(
                    {
                        "success": False,
                        "tool_name": calls[i].get("tool_name", "unknown"),
                        "result": None,
                        "error": str(result),
                        "duration_ms": 0,
                        "timed_out": False,
                    }
                )
            else:
                processed.append(result)

        return processed

    def list_executable_tools(self, category: str | None = None) -> list[dict[str, Any]]:
        """List all tools available for execution.

        Args:
            category: Optional category filter.

        Returns:
            List of tool definition dictionaries.
        """
        return self.registry.list_tools(category=category)
