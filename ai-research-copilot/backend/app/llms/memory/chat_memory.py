"""
Token-aware chat memory manager.

Tracks conversation messages and automatically trims older messages
when the estimated token count exceeds a configurable ceiling, ensuring
that the conversation stays within model context-window limits.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Rough estimate: 1 token ≈ 4 characters for English text.
_CHARS_PER_TOKEN = 4


class ChatMemory:
    """
    Manages a rolling window of chat messages bounded by a token budget.

    Messages are stored as ``{"role": str, "content": str}`` dicts.
    When the estimated total token count exceeds ``max_tokens``, the
    oldest messages (after the system message, if present) are removed
    first.

    Example::

        memory = ChatMemory(max_tokens=8000)
        memory.add("system", "You are a helpful assistant.")
        memory.add("user", "Hello!")
        memory.add("assistant", "Hi there!")
        print(memory.get_token_count())  # ≈ tokens used
        msgs = memory.get_messages()     # list of dicts
    """

    def __init__(self, max_tokens: int = 8000) -> None:
        """
        Initialise the chat memory.

        Args:
            max_tokens: Maximum estimated token budget for the stored messages.
        """
        self.max_tokens = max_tokens
        self.messages: list[dict[str, str]] = []
        logger.debug("ChatMemory created with max_tokens=%d", max_tokens)

    def add(self, role: str, content: str) -> None:
        """
        Add a message to memory and trim if necessary.

        Args:
            role: Message role (``system``, ``user``, ``assistant``).
            content: Message content string.
        """
        self.messages.append({"role": role, "content": content})
        self.trim()

    def get_messages(self) -> list[dict[str, str]]:
        """
        Return a copy of the current message list.

        Returns:
            List of message dicts safe to pass directly to an LLM.
        """
        return list(self.messages)

    def get_token_count(self) -> int:
        """
        Estimate the total number of tokens across all stored messages.

        Uses a simple character-based heuristic. For more accurate counts
        you should use the provider's tokenizer, but this is sufficient
        for memory management decisions.
        """
        total_chars = sum(len(m.get("content", "")) for m in self.messages)
        return total_chars // _CHARS_PER_TOKEN

    def trim(self) -> None:
        """
        Remove oldest messages until the token budget is respected.

        The system message (first message with ``role == "system"``) is
        always preserved. Messages are removed from the oldest
        non-system position inward.
        """
        while self.get_token_count() > self.max_tokens and len(self.messages) > 1:
            # Find the first removable message index (skip system at index 0).
            remove_idx = 1 if self.messages[0].get("role") == "system" else 0
            if remove_idx >= len(self.messages):
                break
            removed = self.messages.pop(remove_idx)
            logger.debug(
                "Trimmed message: role=%s, content_len=%d",
                removed.get("role"),
                len(removed.get("content", "")),
            )

    def clear(self) -> None:
        """Remove all messages from memory."""
        self.messages.clear()
        logger.debug("ChatMemory cleared")

    def get_last_user_message(self) -> str | None:
        """Return the content of the most recent user message, or ``None``."""
        for msg in reversed(self.messages):
            if msg["role"] == "user":
                return msg["content"]
        return None

    def get_last_assistant_message(self) -> str | None:
        """Return the content of the most recent assistant message, or ``None``."""
        for msg in reversed(self.messages):
            if msg["role"] == "assistant":
                return msg["content"]
        return None

    def remove_message_at(self, index: int) -> dict[str, str]:
        """
        Remove and return the message at *index*.

        Args:
            index: Zero-based position in the message list.

        Returns:
            The removed message dict.

        Raises:
            IndexError: If *index* is out of range.
        """
        return self.messages.pop(index)

    def to_dict(self) -> dict[str, Any]:
        """
        Serialise the memory state for persistence.

        Returns:
            Dict with ``messages`` and ``max_tokens`` keys.
        """
        return {
            "messages": self.get_messages(),
            "max_tokens": self.max_tokens,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChatMemory":
        """
        Reconstruct a ``ChatMemory`` from a serialised dict.

        Args:
            data: Dict as produced by ``to_dict()``.

        Returns:
            A new ``ChatMemory`` instance.
        """
        instance = cls(max_tokens=data.get("max_tokens", 8000))
        for msg in data.get("messages", []):
            instance.messages.append(
                {"role": msg["role"], "content": msg["content"]}
            )
        return instance

    def __len__(self) -> int:
        return len(self.messages)

    def __repr__(self) -> str:
        return (
            f"ChatMemory(messages={len(self.messages)}, "
            f"tokens≈{self.get_token_count()}/{self.max_tokens})"
        )
