"""
Planner agent – breaks complex tasks into ordered, actionable steps.

The planner decomposes a high-level goal into concrete sub-steps, identifies
dependencies between them, and estimates effort.
"""

import json
import uuid
import logging
from typing import Any

from app.agents.base.agent import BaseAgent
from app.llms.providers.base import BaseLLMProvider
from app.llms.prompts.templates import PLANNER_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class PlannerAgent(BaseAgent):
    """Creates step-by-step plans for complex requests.

    Workflow:
    1. Parse the user's goal and any constraints.
    2. Generate an ordered list of concrete steps.
    3. Identify inter-step dependencies.
    4. Estimate overall effort.
    """

    agent_type: str = "planner"

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
        """Create a step-by-step plan for the given request.

        Parameters
        ----------
        input_data : dict
            ``"message"``: the high-level goal or task description.
            ``"constraints"`` (optional): list of constraints to respect.
            ``"max_steps"`` (optional): maximum number of steps (default 10).

        Returns
        -------
        dict
            ``{"plan_title": …, "steps": …, "estimated_effort": …,
            "dependencies": …}``
        """
        message = input_data.get("message", "")
        if not message:
            return {"plan_title": "", "steps": [], "estimated_effort": "low", "dependencies": [], "error": "No message provided."}

        self.logger.info("Planner agent processing: %r", message[:120])
        self.memory.add("user", message)

        constraints = input_data.get("constraints", [])
        max_steps = input_data.get("max_steps", 10)

        plan = await self._generate_plan(message, constraints, max_steps)
        enriched = await self._enrich_plan(plan, message)

        self.memory.add("assistant", json.dumps(enriched, default=str))
        return enriched

    # ------------------------------------------------------------------
    # Internal steps
    # ------------------------------------------------------------------

    async def _generate_plan(
        self,
        goal: str,
        constraints: list[str],
        max_steps: int,
    ) -> dict[str, Any]:
        """Ask the LLM to produce a structured plan."""
        prompt = (
            f"Create a detailed step-by-step plan for the following goal.\n\n"
            f"Goal: {goal}\n\n"
        )
        if constraints:
            prompt += f"Constraints:\n" + "\n".join(f"- {c}" for c in constraints) + "\n\n"
        prompt += (
            f"Generate at most {max_steps} steps.\n\n"
            "Respond with a JSON object:\n"
            '{"plan_title": "...", "steps": [...], "estimated_effort": "low|medium|high"}\n\n'
            "Each step must have: "
            '{"step_id": <int>, "title": "...", "description": "...", '
            '"difficulty": "easy|medium|hard", "depends_on": [<step_ids>]}'
        )

        messages = self._build_messages(PLANNER_SYSTEM_PROMPT, prompt)
        response = await self._generate_response(messages, temperature=0.4, max_tokens=3000)
        parsed = self._parse_json_response(response)

        if isinstance(parsed, dict):
            parsed.setdefault("plan_title", goal[:100])
            parsed.setdefault("steps", [])
            parsed.setdefault("estimated_effort", "medium")
            parsed.setdefault("dependencies", [])
            return parsed

        return {
            "plan_title": goal[:100],
            "steps": [],
            "estimated_effort": "medium",
            "dependencies": [],
        }

    async def _enrich_plan(
        self, plan: dict[str, Any], original_goal: str
    ) -> dict[str, Any]:
        """Validate and enrich the plan with dependency metadata."""
        steps = plan.get("steps", [])
        if not steps:
            return plan

        # Build a dependency graph for metadata
        dep_graph: dict[int, list[int]] = {}
        for step in steps:
            sid = step.get("step_id", 0)
            deps = step.get("depends_on", [])
            dep_graph[sid] = deps

        # Identify steps that can run in parallel
        ready_steps: list[int] = []
        blocked_steps: list[int] = []
        for sid, deps in dep_graph.items():
            if not deps:
                ready_steps.append(sid)
            else:
                blocked_steps.append(sid)

        plan["parallel_groups"] = {
            "ready_now": ready_steps,
            "blocked": blocked_steps,
        }

        # Recompute dependencies as a flat list of pairs
        flat_deps: list[dict[str, Any]] = []
        for sid, deps in dep_graph.items():
            for dep in deps:
                flat_deps.append({"from": dep, "to": sid})
        plan["dependencies"] = flat_deps

        return plan
