"""
Conversation chain for multi-turn LLM interactions.

Wraps an LLM provider with conversation memory, prompt templating,
and optional RAG context injection.
"""

import logging
import uuid
from dataclasses import dataclass, field
from typing import Any

from app.llms.providers.base import BaseLLMProvider, LLMResponse
from app.llms.memory.chat_memory import ChatMemory

logger = logging.getLogger(__name__)


@dataclass
class ChainConfig:
    """Configuration for a conversation chain."""

    system_prompt: str = "You are ARC, an AI Research Copilot. You are professional, intelligent, and helpful."
    max_context_tokens: int = 8000
    temperature: float = 0.7
    max_tokens: int = 4096
    model: str | None = None
    rag_context: str | None = None


class ConversationChain:
    """Manages a multi-turn conversation with an LLM.

    Maintains per-conversation memory so that multiple conversation threads
    can coexist within the same chain instance.

    Parameters
    ----------
    llm_provider : BaseLLMProvider
        The LLM backend used to generate responses.
    config : ChainConfig | None
        Optional configuration overrides.
    """

    def __init__(
        self,
        llm_provider: BaseLLMProvider,
        config: ChainConfig | None = None,
    ) -> None:
        self.llm = llm_provider
        self.config = config or ChainConfig()
        self._memories: dict[str, ChatMemory] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def predict(
        self,
        user_input: str,
        conversation_id: uuid.UUID | str | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Send a user message and return the LLM response.

        Parameters
        ----------
        user_input : str
            The user's latest message.
        conversation_id : uuid.UUID | str | None
            Conversation identifier. A new UUID is generated when *None*.
        **kwargs
            Extra parameters forwarded to the LLM provider.

        Returns
        -------
        LLMResponse
            The model's reply wrapped in the standard response envelope.
        """
        cid = str(conversation_id) if conversation_id else str(uuid.uuid4())
        memory = self._get_memory(cid)
        memory.add("user", user_input)

        messages = self._build_messages(memory)
        temperature = kwargs.pop("temperature", self.config.temperature)
        max_tokens = kwargs.pop("max_tokens", self.config.max_tokens)
        model = kwargs.pop("model", self.config.model)

        response = await self.llm.generate(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

        memory.add("assistant", response.content)
        return response

    async def predict_stream(self, user_input: str, conversation_id: uuid.UUID | str | None = None, **kwargs: Any):  # type: ignore[return]
        """Stream a response token-by-token."""
        cid = str(conversation_id) if conversation_id else str(uuid.uuid4())
        memory = self._get_memory(cid)
        memory.add("user", user_input)

        messages = self._build_messages(memory)
        temperature = kwargs.pop("temperature", self.config.temperature)
        max_tokens = kwargs.pop("max_tokens", self.config.max_tokens)
        model = kwargs.pop("model", self.config.model)

        full_content: list[str] = []
        async for chunk in self.llm.generate_stream(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        ):
            full_content.append(chunk)
            yield chunk

        memory.add("assistant", "".join(full_content))

    def get_memory(self, conversation_id: uuid.UUID | str | None = None) -> ChatMemory:
        """Expose memory for a conversation (read-only intent)."""
        cid = str(conversation_id) if conversation_id else str(uuid.uuid4())
        return self._get_memory(cid)

    def clear_memory(self, conversation_id: uuid.UUID | str | None = None) -> None:
        """Clear the memory for a specific conversation."""
        cid = str(conversation_id) if conversation_id else ""
        if cid in self._memories:
            self._memories[cid].clear()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_memory(self, conversation_id: str) -> ChatMemory:
        if conversation_id not in self._memories:
            self._memories[conversation_id] = ChatMemory(
                max_tokens=self.config.max_context_tokens,
            )
        return self._memories[conversation_id]

    def _build_messages(self, memory: ChatMemory) -> list[dict[str, str]]:
        """Build the full message list including system prompt and RAG context."""
        messages: list[dict[str, str]] = []
        system_parts: list[str] = [self.config.system_prompt]
        if self.config.rag_context:
            system_parts.append(
                f"\nRelevant context from documents:\n{self.config.rag_context}"
            )
        messages.append({"role": "system", "content": "\n".join(system_parts)})
        messages.extend(memory.get_messages())
        return messages
