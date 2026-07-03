"""
Automation agent – designs and executes automated workflows.
"""

import json
import uuid
import logging
from typing import Any

from app.agents.base.agent import BaseAgent
from app.llms.providers.base import BaseLLMProvider
from app.llms.prompts.templates import AUTOMATION_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class AutomationAgent(BaseAgent):
    """Designs and orchestrates automated workflows.

    The agent:
    1. Parses the automation request into trigger → action → condition steps.
    2. Generates a reproducible workflow definition.
    3. Optionally executes the workflow steps via tool-calling.
    """

    agent_type: str = "automation"

    def __init__(self, llm_provider: BaseLLMProvider, config: dict[str, Any] | None = None) -> None:
        super().__init__(llm_provider, config)

    # ------------------------------------------------------------------
    # Core interface
    # ------------------------------------------------------------------

    async def execute(
        self,
        input_data: dict[str, Any],
        conversation_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        """Design an automation workflow for the given request.

        Parameters
        ----------
        input_data : dict
            ``"message"``: description of the automation goal.
            ``"existing_workflow"`` (optional): workflow to modify or extend.
            ``"execute"`` (optional): if ``True``, run the workflow steps
            (only for safe, idempotent actions).

        Returns
        -------
        dict
            ``{"workflow_name": …, "trigger": …, "steps": …,
            "error_handling": …, "estimated_duration": …, "status": …}``
        """
        message = input_data.get("message", "")
        if not message:
            return {
                "workflow_name": "",
                "trigger": {},
                "steps": [],
                "error_handling": {},
                "estimated_duration": "",
                "status": "error",
                "error": "No message provided.",
            }

        self.logger.info("Automation agent processing: %r", message[:120])
        self.memory.add("user", message)

        existing = input_data.get("existing_workflow")

        # Step 1 – design the workflow
        workflow = await self._design_workflow(message, existing)

        # Step 2 – validate the workflow
        validation = await self._validate_workflow(workflow)

        # Step 3 – optionally execute
        should_execute = input_data.get("execute", False)
        execution_results: list[dict[str, Any]] = []
        if should_execute:
            execution_results = await self._execute_workflow(workflow)

        result = {
            **workflow,
            "validation": validation,
            "execution_results": execution_results,
            "status": "completed" if not execution_results else "executed",
        }

        self.memory.add("assistant", json.dumps(result, default=str))
        return result

    # ------------------------------------------------------------------
    # Internal steps
    # ------------------------------------------------------------------

    async def _design_workflow(
        self, goal: str, existing_workflow: dict[str, Any] | None
    ) -> dict[str, Any]:
        """Use the LLM to produce a workflow definition."""
        prompt_parts = [
            "Design a workflow automation for the following request.\n"
            "Include trigger, ordered steps, conditions, and error handling.\n\n"
            f"Request: {goal}\n",
        ]
        if existing_workflow:
            prompt_parts.append(
                f"\nExisting workflow to modify:\n"
                f"{json.dumps(existing_workflow, default=str)[:3000]}\n"
            )
        prompt_parts.append(
            "\nRespond with a JSON object:\n"
            '{"workflow_name": "...", "trigger": {"type": "...", "config": {...}}, '
            '"steps": [{"step_id": 1, "action": "...", "params": {...}, '
            '"condition": "...", "on_error": "stop|skip|retry"}], '
            '"error_handling": {"strategy": "...", "max_retries": ...}, '
            '"estimated_duration": "..."}'
        )

        messages = self._build_messages(AUTOMATION_SYSTEM_PROMPT, "\n".join(prompt_parts))
        try:
            response = await self._generate_response(messages, temperature=0.3, max_tokens=3000)
            parsed = self._parse_json_response(response)
            if isinstance(parsed, dict):
                parsed.setdefault("workflow_name", goal[:100])
                parsed.setdefault("trigger", {"type": "manual", "config": {}})
                parsed.setdefault("steps", [])
                parsed.setdefault("error_handling", {"strategy": "stop", "max_retries": 3})
                parsed.setdefault("estimated_duration", "unknown")
                return parsed
        except Exception:
            self.logger.exception("Workflow design failed")

        return {
            "workflow_name": goal[:100],
            "trigger": {"type": "manual", "config": {}},
            "steps": [],
            "error_handling": {"strategy": "stop", "max_retries": 3},
            "estimated_duration": "unknown",
        }

    async def _validate_workflow(self, workflow: dict[str, Any]) -> dict[str, Any]:
        """Validate the workflow structure and identify potential issues."""
        steps = workflow.get("steps", [])
        issues: list[str] = []

        # Check for empty steps
        if not steps:
            issues.append("Workflow has no steps.")

        # Check for circular dependencies in step ordering
        step_ids = [s.get("step_id") for s in steps if isinstance(s, dict)]
        if len(step_ids) != len(set(step_ids)):
            issues.append("Duplicate step IDs found.")

        # Ask the LLM for a deeper validation
        prompt = (
            "Validate the following workflow definition. Check for:\n"
            "- Missing required fields\n"
            "- Logical errors in step ordering\n"
            "- Missing error handling\n"
            "- Potential security concerns\n\n"
            f"Workflow:\n{json.dumps(workflow, default=str)[:4000]}\n\n"
            "Respond with a JSON object:\n"
            '{"valid": true|false, "issues": [...], "warnings": [...], '
            '"suggestions": [...]}'
        )

        messages = self._build_messages(AUTOMATION_SYSTEM_PROMPT, prompt)
        try:
            response = await self._generate_response(messages, temperature=0.2, max_tokens=1000)
            parsed = self._parse_json_response(response)
            if isinstance(parsed, dict):
                parsed.setdefault("valid", len(issues) == 0)
                parsed.setdefault("issues", issues)
                parsed.setdefault("warnings", [])
                parsed.setdefault("suggestions", [])
                return parsed
        except Exception:
            self.logger.exception("Workflow validation LLM call failed")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": [],
            "suggestions": [],
        }

    async def _execute_workflow(
        self, workflow: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Simulate or execute workflow steps.

        In a production system this would call real tool APIs.
        Here we log each step and return a simulated result.
        """
        steps = workflow.get("steps", [])
        results: list[dict[str, Any]] = []

        for step in steps:
            step_id = step.get("step_id", "?")
            action = step.get("action", "unknown")
            self.logger.info("Executing step %s: %s", step_id, action)

            result_entry = {
                "step_id": step_id,
                "action": action,
                "status": "completed",
                "output": f"Step {step_id} executed successfully.",
                "simulated": True,
            }

            # Check condition if present
            condition = step.get("condition")
            if condition and condition.lower() in ("false", "skip", "0"):
                result_entry["status"] = "skipped"
                result_entry["output"] = f"Step {step_id} skipped (condition not met)."

            results.append(result_entry)

        return results
