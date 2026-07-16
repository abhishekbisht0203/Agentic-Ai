"""
Supervisor agent – analyses user intent and delegates to specialist agents.

The Supervisor is the entry point for every user request.  It classifies the
intent, selects the most appropriate agent type, and builds a context payload
that the downstream agent can consume.
"""

import json
import uuid
import logging
from typing import Any

from app.agents.base.agent import BaseAgent
from app.llms.providers.base import BaseLLMProvider, LLMResponse
from app.llms.prompts.templates import SUPERVISOR_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

# Canonical mapping of intent keywords → agent types for rule-based fallback.
_INTENT_KEYWORDS: dict[str, list[str]] = {
    "research": ["research", "find", "search", "investigate", "look up", "explore"],
    "planner": ["plan", "step-by-step", "break down", "roadmap", "organise"],
    "data_analyst": ["data", "statistics", "chart", "graph", "analyse", "dataset"],
    "critic": ["review", "critique", "evaluate", "feedback", "improve"],
    "code_assistant": ["code", "program", "function", "debug", "python", "javascript", "api"],
    "cli_agent": ["terminal", "cli", "shell", "command line", "execute", "run command"],
    "automation": ["automate", "workflow", "schedule", "batch", "pipeline"],
    "document_qa": ["document", "pdf", "paper", "article", "upload", "rag"],
    "memory": ["remember", "save", "store", "recall", "preference"],
    "general": ["hello", "hi", "help", "chat"],
}

_VALID_AGENT_TYPES = {
    "research",
    "planner",
    "data_analyst",
    "critic",
    "code_assistant",
    "cli_agent",
    "automation",
    "document_qa",
    "memory",
    "general",
}


class SupervisorAgent(BaseAgent):
    """Analyses user intent and delegates to the appropriate specialist agent.

    The supervisor never produces a final answer itself; it only decides
    *which* agent should handle the request and prepares the context.
    """

    agent_type: str = "supervisor"

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
        """Analyse the user request, plan tasks, and delegate.

        Parameters
        ----------
        input_data : dict
            Must contain a ``"message"`` key with the user's text.
            Optional keys: ``"agent_type"`` (force a specific agent),
            ``"context"`` (extra context for the chosen agent).
        conversation_id : uuid.UUID | None
            Conversation identifier for multi-turn memory.

        Returns
        -------
        dict
            ``{"intent": …, "agent_type": …, "priority": …, "context": …,
            "delegation": <agent-specific input payload>}``
        """
        message = input_data.get("message", "")
        if not message:
            return {
                "intent": "empty",
                "agent_type": "general",
                "priority": 5,
                "context": "",
                "delegation": {"message": ""},
                "error": "No message provided.",
            }

        self.logger.info("Supervisor processing: %r", message[:120])
        self.memory.add("user", message)

        forced_agent = input_data.get("agent_type")
        if forced_agent and forced_agent in _VALID_AGENT_TYPES:
            intent_result = {
                "intent": f"User-requested agent: {forced_agent}",
                "agent_type": forced_agent,
                "priority": 3,
                "context": input_data.get("context", ""),
            }
        else:
            intent_result = await self._detect_intent(message)

        task_plan = await self._plan_tasks(intent_result, message)

        delegation = {
            "message": message,
            "conversation_id": str(conversation_id) if conversation_id else None,
            "context": intent_result.get("context", ""),
            "tasks": task_plan,
        }

        result = {
            **intent_result,
            "delegation": delegation,
        }
        self.memory.add("assistant", json.dumps(result, default=str))
        return result

    # ------------------------------------------------------------------
    # Intent detection
    # ------------------------------------------------------------------

    async def _detect_intent(self, message: str) -> dict[str, Any]:
        """Detect user intent from the message.

        First attempts an LLM-based classification; falls back to
        keyword matching if the LLM call fails.
        """
        try:
            return await self._llm_classify_intent(message)
        except Exception:
            self.logger.warning("LLM intent classification failed, using keyword fallback")
            return self._keyword_classify_intent(message)

    async def _llm_classify_intent(self, message: str) -> dict[str, Any]:
        """Use the LLM to classify intent into a structured dict."""
        classification_prompt = (
            "Classify the following user message into an intent, the most "
            "appropriate agent type, and a priority (1=highest, 5=lowest).\n"
            "Also extract any extra context that would help the downstream agent.\n\n"
            f"Available agent types: {', '.join(sorted(_VALID_AGENT_TYPES))}\n\n"
            f"User message: {message}\n\n"
            "Respond with a JSON object only."
        )
        messages = self._build_messages(SUPERVISOR_SYSTEM_PROMPT, classification_prompt)
        response = await self._generate_response(messages, temperature=0.3, max_tokens=512)
        parsed = self._parse_json_response(response)

        agent_type = parsed.get("agent_type", "general")
        if agent_type not in _VALID_AGENT_TYPES:
            agent_type = self._keyword_fallback_agent(message)

        return {
            "intent": parsed.get("intent", message[:100]),
            "agent_type": agent_type,
            "priority": int(parsed.get("priority", 3)),
            "context": parsed.get("context", ""),
        }

    def _keyword_classify_intent(self, message: str) -> dict[str, Any]:
        """Simple keyword-based intent classification."""
        lower_msg = message.lower()
        best_agent = "general"
        best_score = 0

        for agent, keywords in _INTENT_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in lower_msg)
            if score > best_score:
                best_score = score
                best_agent = agent

        return {
            "intent": f"Keyword match for '{best_agent}'",
            "agent_type": best_agent,
            "priority": 3 if best_score > 0 else 5,
            "context": "",
        }

    def _keyword_fallback_agent(self, message: str) -> str:
        """Fast keyword-based fallback when LLM returns an unknown agent."""
        lower_msg = message.lower()
        best_agent = "general"
        best_score = 0
        for agent, keywords in _INTENT_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in lower_msg)
            if score > best_score:
                best_score = score
                best_agent = agent
        return best_agent

    # ------------------------------------------------------------------
    # Task planning
    # ------------------------------------------------------------------

    async def _plan_tasks(
        self,
        intent: dict[str, Any],
        message: str,
    ) -> list[dict[str, Any]]:
        """Create a simple task plan based on the detected intent.

        Returns a list of task descriptors.  For most single-agent requests
        this will be a single-element list.
        """
        agent_type = intent.get("agent_type", "general")
        tasks: list[dict[str, Any]] = [
            {
                "task_id": 1,
                "agent_type": agent_type,
                "description": message[:200],
                "priority": intent.get("priority", 3),
                "status": "pending",
            }
        ]

        # If this looks like a complex request, suggest follow-up tasks.
        if agent_type == "research":
            tasks.append(
                {
                    "task_id": 2,
                    "agent_type": "critic",
                    "description": "Review and validate research findings",
                    "priority": 4,
                    "status": "pending",
                    "depends_on": [1],
                }
            )
        elif agent_type == "planner":
            tasks.append(
                {
                    "task_id": 2,
                    "agent_type": "research",
                    "description": "Gather information needed for plan execution",
                    "priority": 3,
                    "status": "pending",
                    "depends_on": [1],
                }
            )

        return tasks
