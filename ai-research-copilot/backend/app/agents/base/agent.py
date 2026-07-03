"""
Abstract base class for every AI agent in the system.

All concrete agents inherit from ``BaseAgent`` and implement the
``execute`` method.  The base class provides common infrastructure:
LLM interaction with retries, conversation memory, message building,
and standardised serialisation.
"""

import json
import uuid
import logging
import asyncio
from abc import ABC, abstractmethod
from typing import Any

from app.llms.providers.base import BaseLLMProvider, LLMResponse
from app.llms.memory.chat_memory import ChatMemory

logger = logging.getLogger(__name__)

# Default retry configuration
_MAX_RETRIES = 3
_RETRY_DELAY = 1.0  # seconds – doubles on each retry


class BaseAgent(ABC):
    """Abstract base class for all AI agents.

    Subclasses **must** override:
    - ``agent_type``: a short string identifier (e.g. ``"research"``).
    - ``execute``: the main entry point for processing a request.

    Parameters
    ----------
    llm_provider : BaseLLMProvider
        The LLM backend used by the agent.
    config : dict | None
        Optional configuration overrides.  Recognised keys include
        ``max_context_tokens``, ``max_retries``, ``temperature``,
        ``max_tokens``, and ``model``.
    """

    agent_type: str = "base"

    def __init__(
        self,
        llm_provider: BaseLLMProvider,
        config: dict[str, Any] | None = None,
    ) -> None:
        self.llm = llm_provider
        self.config: dict[str, Any] = config or {}
        self.memory = ChatMemory(
            max_tokens=self.config.get("max_context_tokens", 8000),
        )
        self.logger = logging.getLogger(f"agent.{self.agent_type}")
        self._max_retries: int = self.config.get("max_retries", _MAX_RETRIES)
        self._retry_delay: float = self.config.get("retry_delay", _RETRY_DELAY)

    # ------------------------------------------------------------------
    # Core interface
    # ------------------------------------------------------------------

    @abstractmethod
    async def execute(
        self,
        input_data: dict[str, Any],
        conversation_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        """Execute the agent with the given input.

        Parameters
        ----------
        input_data : dict
            Payload containing at least a ``"message"`` key (for most agents).
        conversation_id : uuid.UUID | None
            Optional conversation identifier for multi-turn interactions.

        Returns
        -------
        dict
            Agent-specific output dictionary.
        """
        ...

    # ------------------------------------------------------------------
    # LLM helpers
    # ------------------------------------------------------------------

    async def _generate_response(
        self,
        messages: list[dict[str, str]],
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate an LLM response with automatic retries.

        Parameters
        ----------
        messages : list[dict[str, str]]
            Full message list (system + history + user).
        **kwargs
            Extra parameters forwarded to ``llm.generate``.

        Returns
        -------
        LLMResponse

        Raises
        ------
        RuntimeError
            If all retry attempts fail.
        """
        temperature = kwargs.pop("temperature", self.config.get("temperature", 0.7))
        max_tokens = kwargs.pop("max_tokens", self.config.get("max_tokens", 4096))
        model = kwargs.pop("model", self.config.get("model"))

        last_error: Exception | None = None
        delay = self._retry_delay

        for attempt in range(1, self._max_retries + 1):
            try:
                response = await self.llm.generate(
                    messages=messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )
                self.logger.debug(
                    "LLM response received (attempt %d, tokens=%d)",
                    attempt,
                    response.token_usage.get("total_tokens", 0),
                )
                return response
            except Exception as exc:
                last_error = exc
                self.logger.warning(
                    "LLM call failed (attempt %d/%d): %s",
                    attempt,
                    self._max_retries,
                    exc,
                )
                if attempt < self._max_retries:
                    await asyncio.sleep(delay)
                    delay *= 2

        raise RuntimeError(
            f"LLM call failed after {self._max_retries} attempts: {last_error}"
        )

    def _build_messages(
        self,
        system_prompt: str,
        user_message: str,
        include_history: bool = True,
    ) -> list[dict[str, str]]:
        """Build the message list for an LLM call.

        Parameters
        ----------
        system_prompt : str
            The system-level instruction for this agent.
        user_message : str
            The user's current message.
        include_history : bool
            Whether to prepend conversation history from memory.

        Returns
        -------
        list[dict[str, str]]
            Messages in the ``{"role": …, "content": …}`` format.
        """
        messages: list[dict[str, str]] = [
            {"role": "system", "content": system_prompt},
        ]
        if include_history:
            messages.extend(self.memory.get_messages())
        messages.append({"role": "user", "content": user_message})
        return messages

    def _get_system_prompt(self) -> str:
        """Return the system prompt for this agent.

        Subclasses should override this method to supply a specialised prompt.
        The default returns a generic assistant prompt.
        """
        return "You are a helpful AI assistant."

    def _parse_json_response(self, response: LLMResponse) -> dict[str, Any]:
        """Best-effort extraction of a JSON object from LLM output.

        If the response is already valid JSON, return it directly.  Otherwise,
        try to find a JSON block inside a markdown code-fence and parse that.
        Falls back to ``{"raw": <original text>}`` if nothing works.
        """
        text = response.content.strip()
        # Direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        # Extract from code-fence
        if "```" in text:
            parts = text.split("```")
            for part in parts[1::2]:  # odd-indexed parts are inside fences
                candidate = part.strip()
                if candidate.startswith(("json\n", "json\r")):
                    candidate = candidate.split("\n", 1)[-1]
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    continue
        return {"raw": response.content}

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Serialise agent metadata."""
        return {
            "agent_type": self.agent_type,
            "config": self.config,
            "memory_size": len(self.memory),
        }

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(agent_type={self.agent_type!r})"
