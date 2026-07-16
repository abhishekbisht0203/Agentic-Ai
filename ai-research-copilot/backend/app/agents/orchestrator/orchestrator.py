"""
AI Orchestrator – coordinates multiple agents to fulfil complex requests.

The orchestrator is the top-level entry point.  It maintains a registry of
available agents, routes user requests through the supervisor, and
orchestrates multi-agent workflows when a single agent is insufficient.
"""

import asyncio
import json
import uuid
import time
import logging
from typing import Any

from app.agents.base.agent import BaseAgent
from app.agents.supervisor.supervisor import SupervisorAgent
from app.agents.research.research_agent import ResearchAgent
from app.agents.planner.planner import PlannerAgent
from app.agents.data_analyst.data_analyst_agent import DataAnalystAgent
from app.agents.critic.critic_agent import CriticAgent
from app.agents.code_assistant.code_assistant_agent import CodeAssistantAgent
from app.agents.automation.automation_agent import AutomationAgent
from app.agents.document_qa.document_qa_agent import DocumentQAAgent
from app.agents.memory.memory_agent import MemoryAgent
from app.agents.cli_agent.cli_agent import CLIAgent
from app.llms.providers.base import BaseLLMProvider

logger = logging.getLogger(__name__)


class AIOrchestrator:
    """Coordinates multiple agents to fulfil complex requests.

    The orchestrator:
    1. Receives a user request.
    2. Asks the Supervisor to classify intent and select the primary agent.
    3. Routes the request to that agent.
    4. Optionally follows up with secondary agents (e.g. critic review).

    Parameters
    ----------
    llm_provider : BaseLLMProvider
        Shared LLM backend used by all agents.
    """

    def __init__(self, llm_provider: BaseLLMProvider) -> None:
        self.llm = llm_provider
        self.agents: dict[str, BaseAgent] = {}
        self.supervisor = SupervisorAgent(llm_provider)
        self._register_default_agents(llm_provider)

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def _register_default_agents(self, llm: BaseLLMProvider) -> None:
        """Register the built-in agent set."""
        for agent_cls in (
            ResearchAgent,
            PlannerAgent,
            DataAnalystAgent,
            CriticAgent,
            CodeAssistantAgent,
            AutomationAgent,
            DocumentQAAgent,
            MemoryAgent,
            CLIAgent,
        ):
            agent = agent_cls(llm)
            self.agents[agent.agent_type] = agent
        logger.info("Registered default agents: %s", list(self.agents.keys()))

    def register_agent(self, agent: BaseAgent) -> None:
        """Register a custom agent, overriding any existing type."""
        self.agents[agent.agent_type] = agent
        logger.info("Registered agent: %s", agent.agent_type)

    def get_agent(self, agent_type: str) -> BaseAgent | None:
        """Retrieve an agent by type."""
        return self.agents.get(agent_type)

    def list_agents(self) -> list[dict[str, Any]]:
        """Return metadata for all registered agents."""
        return [a.to_dict() for a in self.agents.values()]

    # ------------------------------------------------------------------
    # Routing
    # ------------------------------------------------------------------

    async def route_request(
        self,
        message: str,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID | None = None,
        agent_type: str | None = None,
    ) -> dict[str, Any]:
        """Route a user request to the appropriate agent(s).

        Parameters
        ----------
        message : str
            The user's message.
        user_id : uuid.UUID
            Identifier of the requesting user.
        conversation_id : uuid.UUID | None
            Optional conversation identifier for multi-turn memory.
        agent_type : str | None
            If provided, skip supervisor classification and use this agent.

        Returns
        -------
        dict
            ``{"agent_type": …, "result": …, "execution_time_ms": …,
            "secondary_results": …}``
        """
        start = time.monotonic()
        logger.info(
            "Routing request from user=%s conversation=%s",
            user_id,
            conversation_id,
        )

        # If the caller already knows the agent, skip the supervisor.
        if agent_type and agent_type in self.agents:
            result = await self.execute_agent(
                agent_type,
                {"message": message, "user_id": str(user_id)},
                conversation_id,
            )
            elapsed = int((time.monotonic() - start) * 1000)
            return {
                "agent_type": agent_type,
                "result": result,
                "execution_time_ms": elapsed,
                "secondary_results": [],
            }

        # Otherwise, ask the supervisor to classify.
        supervisor_input = {
            "message": message,
            "user_id": str(user_id),
        }
        classification = await self.supervisor.execute(
            supervisor_input, conversation_id
        )

        primary_type = classification.get("agent_type", "general")
        delegation = classification.get("delegation", {})

        # Execute the primary agent
        primary_result = await self.execute_agent(
            primary_type,
            {"message": message, "user_id": str(user_id), **delegation},
            conversation_id,
        )

        # Run secondary agents in parallel for speed (Phase 3 optimization)
        secondary_results: list[dict[str, Any]] = []
        tasks = classification.get("tasks", [])
        parallel_tasks = []
        for task in tasks:
            if task.get("status") == "pending" and task.get("agent_type") != primary_type:
                dep_ids = task.get("depends_on", [])
                if dep_ids:
                    parallel_tasks.append(
                        self.execute_agent(
                            task["agent_type"],
                            {
                                "message": message,
                                "user_id": str(user_id),
                                "context": primary_result.get("summary", primary_result.get("explanation", "")),
                            },
                            conversation_id,
                        )
                    )

        if parallel_tasks:
            sec_results = await asyncio.gather(*parallel_tasks, return_exceptions=True)
            for task, sec_result in zip(
                [t for t in tasks if t.get("status") == "pending" and t.get("agent_type") != primary_type and t.get("depends_on")],
                sec_results,
            ):
                if isinstance(sec_result, Exception):
                    logger.error("Secondary agent %s failed: %s", task["agent_type"], sec_result)
                    continue
                secondary_results.append({
                    "agent_type": task["agent_type"],
                    "task_id": task.get("task_id"),
                    "result": sec_result,
                })

        elapsed = int((time.monotonic() - start) * 1000)
        return {
            "agent_type": primary_type,
            "result": primary_result,
            "execution_time_ms": elapsed,
            "secondary_results": secondary_results,
        }

    async def execute_agent(
        self,
        agent_type: str,
        input_data: dict[str, Any],
        conversation_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        """Execute a specific agent by type.

        Parameters
        ----------
        agent_type : str
            Registered agent type identifier.
        input_data : dict
            Payload to pass to the agent's ``execute`` method.
        conversation_id : uuid.UUID | None
            Conversation identifier.

        Returns
        -------
        dict
            The agent's output dictionary.

        Raises
        ------
        ValueError
            If no agent with the given type is registered.
        """
        agent = self.agents.get(agent_type)
        if agent is None:
            raise ValueError(
                f"No agent registered for type '{agent_type}'. "
                f"Available: {list(self.agents.keys())}"
            )

        logger.info("Executing agent: %s", agent_type)
        try:
            result = await agent.execute(input_data, conversation_id)
            return result
        except Exception:
            logger.exception("Agent %s execution failed", agent_type)
            return {
                "error": f"Agent '{agent_type}' execution failed.",
                "agent_type": agent_type,
            }

    # ------------------------------------------------------------------
    # Convenience wrappers
    # ------------------------------------------------------------------

    async def chat(
        self,
        message: str,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID | None = None,
        knowledge_base_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        """High-level chat entry point.

        Routes the message, injects RAG context if a knowledge base is
        specified, and returns a flat response dict.
        """
        extra: dict[str, Any] = {}
        if knowledge_base_id:
            extra["knowledge_base_id"] = str(knowledge_base_id)

        return await self.route_request(
            message=message,
            user_id=user_id,
            conversation_id=conversation_id,
            **extra,
        )
