"""
Workflow Step Executor.

Executes individual workflow steps including tool calls, agent
invocations, condition evaluations, approval gates, and wait
periods. Integrates with the MCP ToolRegistry for tool execution
and provides structured result handling.
"""

import asyncio
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from app.mcp.registry.tool_registry import ToolRegistry
from app.workflows.state.workflow_state import WorkflowState, WorkflowStateStatus

logger = logging.getLogger(__name__)


class StepExecutionError(Exception):
    """Raised when a workflow step fails during execution."""

    def __init__(self, step_name: str, message: str, detail: Any = None) -> None:
        self.step_name = step_name
        self.message = message
        self.detail = detail
        super().__init__(f"Step '{step_name}' failed: {message}")


class StepExecutor:
    """Executes individual workflow steps.

    Dispatches to the appropriate handler based on step type and
    manages step lifecycle events (start, complete, fail).

    Args:
        registry: The MCP ToolRegistry for tool execution.
        timeout: Default timeout for step execution in seconds.
    """

    def __init__(self, registry: ToolRegistry | None = None, timeout: int = 120) -> None:
        self.registry = registry
        self.timeout = timeout
        self._step_handlers: dict[str, Any] = {
            "tool_call": self._handle_tool_call,
            "agent_call": self._handle_agent_call,
            "condition": self._handle_condition,
            "wait": self._handle_wait,
            "approval": self._handle_approval,
            "transform": self._handle_transform,
        }

    async def execute_step(
        self, step: dict[str, Any], state: WorkflowState
    ) -> dict[str, Any]:
        """Execute a single workflow step.

        Validates that all dependencies are satisfied, dispatches to
        the appropriate handler, and records the result in the state.

        Args:
            step: Step definition dictionary with ``id``, ``type``, ``config``.
            state: The current workflow execution state.

        Returns:
            A result dictionary with ``success``, ``output``, ``duration_ms``.

        Raises:
            StepExecutionError: If the step fails and no error recovery is configured.
        """
        step_name = step.get("id", step.get("name", "unknown"))
        step_type = step.get("type", "unknown")
        config = step.get("config", {})

        logger.info(
            "Executing step '%s' (type=%s) in execution %s",
            step_name,
            step_type,
            state.execution_id,
        )

        # Verify dependencies
        dependencies = step.get("dependencies", [])
        for dep in dependencies:
            if dep not in state.step_results:
                raise StepExecutionError(
                    step_name,
                    f"Dependency '{dep}' has not been completed",
                )

        state.mark_step_running(step_name)
        start_time = time.monotonic()

        handler = self._step_handlers.get(step_type)
        if not handler:
            raise StepExecutionError(
                step_name,
                f"Unknown step type: '{step_type}'",
            )

        try:
            result = await handler(step, state, config)
            duration_ms = int((time.monotonic() - start_time) * 1000)

            state.complete_step(step_name, result)

            logger.info(
                "Step '%s' completed in %dms", step_name, duration_ms
            )

            return {
                "success": True,
                "step_name": step_name,
                "step_type": step_type,
                "output": result,
                "duration_ms": duration_ms,
                "error": None,
            }

        except Exception as exc:
            duration_ms = int((time.monotonic() - start_time) * 1000)
            error_msg = str(exc)
            logger.exception(
                "Step '%s' failed after %dms: %s", step_name, duration_ms, error_msg
            )
            raise StepExecutionError(step_name, error_msg) from exc

    async def execute_condition(
        self, condition: dict[str, Any], state: WorkflowState
    ) -> bool:
        """Evaluate a condition against the current workflow state.

        Conditions are simple expressions evaluated against step results
        and input data. Supported operators: ``eq``, ``neq``, ``gt``,
        ``lt``, ``gte``, ``lte``, ``contains``, ``not_contains``,
        ``exists``, ``not_exists``.

        Args:
            condition: Condition definition with ``field``, ``operator``, ``value``.
            state: The current workflow state.

        Returns:
            True if the condition evaluates to True.
        """
        field_path = condition.get("field", "")
        operator_name = condition.get("operator", "eq")
        expected_value = condition.get("value")

        actual_value = self._resolve_field(field_path, state)

        return self._evaluate_operator(actual_value, operator_name, expected_value)

    # ------------------------------------------------------------------
    # Step type handlers
    # ------------------------------------------------------------------

    async def _handle_tool_call(
        self,
        step: dict[str, Any],
        state: WorkflowState,
        config: dict[str, Any],
    ) -> Any:
        """Handle a ``tool_call`` step by invoking an MCP tool.

        Args:
            step: The step definition.
            state: The current workflow state.
            config: Step configuration with ``tool_name`` and ``arguments``.

        Returns:
            The tool execution result.
        """
        tool_name = config.get("tool_name", "")
        if not tool_name:
            raise StepExecutionError(
                step.get("id", "unknown"),
                "tool_call step is missing 'tool_name' in config",
            )

        # Resolve arguments: support template variables from previous steps
        raw_arguments = config.get("arguments", {})
        arguments = self._resolve_templates(raw_arguments, state)

        if self.registry:
            try:
                return await self.registry.execute(tool_name, **arguments)
            except ValueError as exc:
                # Tool not found – return a structured error instead of crashing
                logger.warning("Tool '%s' not found in registry", tool_name)
                return {"error": str(exc), "tool_name": tool_name}
        else:
            logger.warning(
                "No tool registry available for tool_call step '%s'",
                step.get("id", "unknown"),
            )
            return {"tool_name": tool_name, "arguments": arguments, "note": "No registry available"}

    async def _handle_agent_call(
        self,
        step: dict[str, Any],
        state: WorkflowState,
        config: dict[str, Any],
    ) -> Any:
        """Handle an ``agent_call`` step by dispatching to an agent.

        In a full implementation this would call the AgentService.
        Here we prepare the payload and return it for the worker to process.

        Args:
            step: The step definition.
            state: The current workflow state.
            config: Step configuration with ``agent_type``, ``input_data``.

        Returns:
            A payload dictionary for the agent worker.
        """
        agent_type = config.get("agent_type", "general")
        raw_input = config.get("input_data", {})
        resolved_input = self._resolve_templates(raw_input, state)

        return {
            "agent_type": agent_type,
            "input_data": resolved_input,
            "execution_id": str(state.execution_id),
            "workflow_id": str(state.workflow_id),
            "step_id": step.get("id", "unknown"),
        }

    async def _handle_condition(
        self,
        step: dict[str, Any],
        state: WorkflowState,
        config: dict[str, Any],
    ) -> dict[str, Any]:
        """Handle a ``condition`` step.

        Evaluates one or more conditions and returns a result indicating
        which branch should be taken.

        Args:
            step: The step definition.
            state: The current workflow state.
            config: Step configuration with ``conditions`` list.

        Returns:
            A dictionary with ``result`` (bool) and ``branch`` (str).
        """
        conditions = config.get("conditions", [])
        logic = config.get("logic", "and").lower()

        results = []
        for cond in conditions:
            result = await self.execute_condition(cond, state)
            results.append(result)

        if logic == "or":
            combined = any(results)
        else:
            combined = all(results)

        true_branch = config.get("true_branch", "true")
        false_branch = config.get("false_branch", "false")

        return {
            "result": combined,
            "branch": true_branch if combined else false_branch,
            "evaluations": results,
        }

    async def _handle_wait(
        self,
        step: dict[str, Any],
        state: WorkflowState,
        config: dict[str, Any],
    ) -> dict[str, Any]:
        """Handle a ``wait`` step by sleeping for the configured duration.

        Args:
            step: The step definition.
            state: The current workflow state.
            config: Step configuration with ``duration_seconds``.

        Returns:
            A dictionary confirming the wait completed.
        """
        duration = config.get("duration_seconds", 1)
        duration = min(duration, 3600)  # Cap at 1 hour

        logger.info("Wait step sleeping for %ds", duration)
        await asyncio.sleep(duration)

        return {"waited_seconds": duration, "completed_at": datetime.now(timezone.utc).isoformat()}

    async def _handle_approval(
        self,
        step: dict[str, Any],
        state: WorkflowState,
        config: dict[str, Any],
    ) -> dict[str, Any]:
        """Handle an ``approval`` step by pausing execution.

        Sets the state to WAITING_APPROVAL and returns a pending result.
        The actual resumption is handled by the workflow orchestrator.

        Args:
            step: The step definition.
            state: The current workflow state.
            config: Step configuration with ``message`` and ``approvers``.

        Returns:
            A dictionary indicating approval is pending.
        """
        message = config.get("message", "Approval required")
        approvers = config.get("approvers", [])

        state.wait_for_approval()

        return {
            "status": "pending_approval",
            "message": message,
            "approvers": approvers,
            "requested_at": datetime.now(timezone.utc).isoformat(),
        }

    async def _handle_transform(
        self,
        step: dict[str, Any],
        state: WorkflowState,
        config: dict[str, Any],
    ) -> Any:
        """Handle a ``transform`` step by applying data transformations.

        Supports simple field mapping, value injection from previous steps,
        and basic type conversions.

        Args:
            step: The step definition.
            state: The current workflow state.
            config: Step configuration with ``transforms``.

        Returns:
            The transformed data.
        """
        transforms = config.get("transforms", {})
        source_step = config.get("source_step")
        source_data: dict[str, Any] = {}

        if source_step:
            source_data = state.get_step_result(source_step) or {}
        elif state.step_results:
            # Use the most recent step result as source
            last_key = list(state.step_results.keys())[-1]
            source_data = state.step_results[last_key] or {}

        if isinstance(source_data, dict):
            result = dict(source_data)
        else:
            result = {"value": source_data}

        for target_field, mapping in transforms.items():
            if isinstance(mapping, str) and mapping.startswith("$"):
                # Template reference
                ref = mapping[1:]
                result[target_field] = self._resolve_field(ref, state)
            else:
                result[target_field] = mapping

        return result

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _resolve_field(self, field_path: str, state: WorkflowState) -> Any:
        """Resolve a dotted field path against the workflow state.

        Supports paths like:
        - ``input_data.key`` – top-level input
        - ``step_results.step_name.field`` – step output
        - ``step_results.step_name`` – full step result

        Args:
            field_path: Dot-separated field path.
            state: The current workflow state.

        Returns:
            The resolved value, or None if the path is invalid.
        """
        parts = field_path.split(".")
        if not parts:
            return None

        current: Any = None

        if parts[0] == "input_data" and len(parts) > 1:
            current = state.input_data
            parts = parts[1:]
        elif parts[0] == "step_results" and len(parts) > 1:
            step_name = parts[1]
            current = state.step_results.get(step_name)
            parts = parts[2:]
        elif parts[0] == "metadata" and len(parts) > 1:
            current = state.metadata
            parts = parts[1:]
        else:
            return None

        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None

        return current

    def _resolve_templates(
        self, data: Any, state: WorkflowState
    ) -> Any:
        """Recursively resolve template variables in data structures.

        Template variables use the ``${path}`` syntax and are resolved
        against the workflow state.

        Args:
            data: The data structure containing template variables.
            state: The current workflow state.

        Returns:
            The data structure with all templates resolved.
        """
        if isinstance(data, str):
            if data.startswith("${") and data.endswith("}"):
                field_path = data[2:-1]
                return self._resolve_field(field_path, state)
            return data
        if isinstance(data, dict):
            return {
                key: self._resolve_templates(value, state)
                for key, value in data.items()
            }
        if isinstance(data, list):
            return [self._resolve_templates(item, state) for item in data]
        return data

    @staticmethod
    def _evaluate_operator(
        actual: Any, operator_name: str, expected: Any
    ) -> bool:
        """Evaluate a comparison operator.

        Args:
            actual: The actual value from the workflow state.
            operator_name: The operator string.
            expected: The expected value from the condition definition.

        Returns:
            The boolean result of the comparison.
        """
        ops = {
            "eq": lambda a, b: a == b,
            "neq": lambda a, b: a != b,
            "gt": lambda a, b: float(a) > float(b) if a is not None else False,
            "lt": lambda a, b: float(a) < float(b) if a is not None else False,
            "gte": lambda a, b: float(a) >= float(b) if a is not None else False,
            "lte": lambda a, b: float(a) <= float(b) if a is not None else False,
            "contains": lambda a, b: str(b) in str(a) if a is not None else False,
            "not_contains": lambda a, b: str(b) not in str(a) if a is not None else True,
            "exists": lambda a, b: a is not None,
            "not_exists": lambda a, b: a is None,
        }

        handler = ops.get(operator_name)
        if not handler:
            logger.warning("Unknown operator: %s", operator_name)
            return False

        try:
            return handler(actual, expected)
        except (TypeError, ValueError):
            return False
