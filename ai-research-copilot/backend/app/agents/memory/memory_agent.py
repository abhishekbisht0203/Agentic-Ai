"""
Memory agent – extracts and stores important facts from conversations.
"""

import json
import uuid
import logging
from typing import Any

from app.agents.base.agent import BaseAgent
from app.llms.providers.base import BaseLLMProvider
from app.llms.prompts.templates import MEMORY_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class MemoryAgent(BaseAgent):
    """Extracts key information from conversations for long-term storage.

    The memory agent:
    1. Analyses the latest conversation turn(s).
    2. Identifies facts, preferences, decisions, and episodic events.
    3. Categorises and scores each memory for importance.
    4. Returns structured memory entries ready for persistence.
    """

    agent_type: str = "memory"

    def __init__(self, llm_provider: BaseLLMProvider, config: dict[str, Any] | None = None) -> None:
        super().__init__(llm_provider, config)
        self._memory_store: list[dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Core interface
    # ------------------------------------------------------------------

    async def execute(
        self,
        input_data: dict[str, Any],
        conversation_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        """Extract and store memories from the conversation.

        Parameters
        ----------
        input_data : dict
            ``"message"``: the text to extract memories from.
            ``"conversation_history"`` (optional): list of prior messages for context.
            ``"existing_memories"`` (optional): memories already stored (to avoid duplicates).
            ``"user_id"`` (optional): user identifier for scoping.

        Returns
        -------
        dict
            ``{"memories": [...], "summary": …, "total_stored": …}``
        """
        message = input_data.get("message", "")
        if not message:
            return {
                "memories": [],
                "summary": "",
                "total_stored": 0,
                "error": "No message provided.",
            }

        self.logger.info("Memory agent processing: %r", message[:120])
        self.memory.add("user", message)

        conversation_history = input_data.get("conversation_history", [])
        existing_memories = input_data.get("existing_memories", [])
        user_id = input_data.get("user_id")

        # Step 1 – extract memories
        extracted = await self._extract_memories(message, conversation_history, existing_memories)

        # Step 2 – deduplicate against existing
        new_memories = self._deduplicate(extracted, existing_memories)

        # Step 3 – store
        stored = self._store_memories(new_memories, user_id, conversation_id)

        # Step 4 – summarise
        summary = await self._summarise_extraction(message, stored)

        result = {
            "memories": stored,
            "summary": summary,
            "total_stored": len(stored),
        }

        self.memory.add("assistant", json.dumps(result, default=str))
        return result

    # ------------------------------------------------------------------
    # Internal steps
    # ------------------------------------------------------------------

    async def _extract_memories(
        self,
        message: str,
        conversation_history: list[dict[str, str]],
        existing_memories: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Use the LLM to extract memory-worthy information."""
        prompt_parts = [
            "Extract important information from the following text that should "
            "be remembered for future conversations.\n"
        ]
        if conversation_history:
            history_text = "\n".join(
                f"{m.get('role', 'user')}: {m.get('content', '')}"
                for m in conversation_history[-10:]
            )
            prompt_parts.append(f"Recent conversation:\n{history_text}\n")
        prompt_parts.append(f"Latest message: {message}\n")

        if existing_memories:
            memories_text = "\n".join(
                f"- [{m.get('memory_type', '?')}] {m.get('content', '')}"
                for m in existing_memories[:20]
            )
            prompt_parts.append(
                f"\nExisting memories (avoid duplicates):\n{memories_text}\n"
            )

        prompt_parts.append(
            "\nRespond with a JSON object:\n"
            '{"memories": [{"content": "...", '
            '"memory_type": "semantic|factual|episodic|preference", '
            '"importance": "high|medium|low", "source": "..."}], '
            '"summary": "brief summary of what was extracted"}'
        )

        messages = self._build_messages(MEMORY_SYSTEM_PROMPT, "\n".join(prompt_parts))
        try:
            response = await self._generate_response(messages, temperature=0.3, max_tokens=2000)
            parsed = self._parse_json_response(response)
            if isinstance(parsed, dict):
                return parsed.get("memories", [])
            if isinstance(parsed, list):
                return parsed
        except Exception:
            self.logger.exception("Memory extraction failed")

        return []

    def _deduplicate(
        self,
        new_memories: list[dict[str, Any]],
        existing: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Remove memories that are substantially similar to existing ones."""
        existing_contents = {
            m.get("content", "").lower().strip() for m in existing
        }
        unique: list[dict[str, Any]] = []
        for mem in new_memories:
            content = mem.get("content", "").lower().strip()
            if content and content not in existing_contents:
                existing_contents.add(content)
                unique.append(mem)
        return unique

    def _store_memories(
        self,
        memories: list[dict[str, Any]],
        user_id: Any,
        conversation_id: uuid.UUID | None,
    ) -> list[dict[str, Any]]:
        """Persist memories (in-memory store + return for external persistence)."""
        stored: list[dict[str, Any]] = []
        for mem in memories:
            entry = {
                "id": str(uuid.uuid4()),
                "content": mem.get("content", ""),
                "memory_type": mem.get("memory_type", "factual"),
                "importance": mem.get("importance", "medium"),
                "source": mem.get("source", ""),
                "user_id": str(user_id) if user_id else None,
                "conversation_id": str(conversation_id) if conversation_id else None,
                "is_active": True,
            }
            self._memory_store.append(entry)
            stored.append(entry)
        return stored

    async def _summarise_extraction(
        self, original_text: str, stored_memories: list[dict[str, Any]]
    ) -> str:
        """Produce a brief summary of what was extracted."""
        if not stored_memories:
            return "No new memories extracted."

        memories_text = "\n".join(
            f"- [{m.get('memory_type', '?')}] {m.get('content', '')}"
            for m in stored_memories
        )
        prompt = (
            f"Summarise in one sentence what memories were extracted from this text:\n\n"
            f"Original text: {original_text[:500]}\n\n"
            f"Extracted memories:\n{memories_text}"
        )
        messages = self._build_messages(MEMORY_SYSTEM_PROMPT, prompt)
        try:
            response = await self._generate_response(messages, temperature=0.3, max_tokens=200)
            return response.content.strip()
        except Exception:
            self.logger.warning("Memory summarisation failed")
            return f"Extracted {len(stored_memories)} new memories."

    def get_all_stored(self) -> list[dict[str, Any]]:
        """Return all memories stored in this agent instance."""
        return list(self._memory_store)

    def search_stored(self, query: str) -> list[dict[str, Any]]:
        """Search stored memories by content substring."""
        lower_q = query.lower()
        return [m for m in self._memory_store if lower_q in m.get("content", "").lower()]
