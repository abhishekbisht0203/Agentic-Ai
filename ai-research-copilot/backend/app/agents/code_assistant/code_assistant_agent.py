"""
Code Assistant agent – helps with writing, reviewing, debugging, and explaining code.
"""

import json
import uuid
import logging
from typing import Any

from app.agents.base.agent import BaseAgent
from app.llms.providers.base import BaseLLMProvider
from app.llms.prompts.templates import CODE_ASSISTANT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class CodeAssistantAgent(BaseAgent):
    """Assists users with programming tasks.

    Supported task types:
    - ``generate``: write new code from a description.
    - ``review``: review existing code for quality, bugs, and improvements.
    - ``debug``: diagnose and fix bugs.
    - ``explain``: explain how a piece of code works.
    - ``refactor``: suggest refactoring improvements.
    - ``test``: generate unit tests for given code.
    """

    agent_type: str = "code_assistant"

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
        """Assist with a code-related task.

        Parameters
        ----------
        input_data : dict
            ``"message"``: description of the task.
            ``"code"`` (optional): existing code to work with.
            ``"language"`` (optional): programming language hint.
            ``"task_type"`` (optional): one of generate|review|debug|explain|refactor|test.

        Returns
        -------
        dict
            ``{"code": …, "language": …, "explanation": …, "suggestions": …,
            "tests": …, "task_type": …}``
        """
        message = input_data.get("message", "")
        code = input_data.get("code", "")
        language = input_data.get("language", "")
        task_type = input_data.get("task_type", "generate" if not code else "review")

        if not message and not code:
            return {
                "code": "",
                "language": "",
                "explanation": "No message or code provided.",
                "suggestions": [],
                "tests": [],
                "task_type": task_type,
                "error": "No message or code provided.",
            }

        self.logger.info("Code assistant processing task_type=%s", task_type)
        self.memory.add("user", message or f"Task: {task_type} on provided code")

        # Dispatch to the appropriate sub-handler
        handler = {
            "generate": self._generate_code,
            "review": self._review_code,
            "debug": self._debug_code,
            "explain": self._explain_code,
            "refactor": self._refactor_code,
            "test": self._generate_tests,
        }.get(task_type, self._generate_code)

        result = await handler(message, code, language)
        result["task_type"] = task_type

        self.memory.add("assistant", json.dumps(result, default=str))
        return result

    # ------------------------------------------------------------------
    # Task handlers
    # ------------------------------------------------------------------

    async def _generate_code(
        self, description: str, code: str, language: str
    ) -> dict[str, Any]:
        """Generate new code from a description."""
        prompt_parts = [f"Write code for the following requirement.\n"]
        if language:
            prompt_parts.append(f"Language: {language}\n")
        prompt_parts.append(f"Requirement: {description}\n")
        if code:
            prompt_parts.append(f"\nExisting code to build on:\n```\n{code[:4000]}\n```\n")
        prompt_parts.append(
            "\nRespond with a JSON object:\n"
            '{"code": "...", "language": "...", "explanation": "...", '
            '"suggestions": [...], "tests": [...]}'
        )

        messages = self._build_messages(CODE_ASSISTANT_SYSTEM_PROMPT, "\n".join(prompt_parts))
        return await self._extract_code_response(messages, language)

    async def _review_code(
        self, description: str, code: str, language: str
    ) -> dict[str, Any]:
        """Review existing code for quality and issues."""
        prompt_parts = ["Review the following code for correctness, style, performance, and security.\n"]
        if language:
            prompt_parts.append(f"Language: {language}\n")
        prompt_parts.append(f"\nCode:\n```\n{code[:6000]}\n```\n")
        if description:
            prompt_parts.append(f"\nAdditional context: {description}\n")
        prompt_parts.append(
            "\nRespond with a JSON object:\n"
            '{"code": "<improved code>", "language": "...", '
            '"explanation": "<review summary>", "suggestions": [...], '
            '"issues": [{"severity": "...", "description": "...", "line": ...}]}'
        )

        messages = self._build_messages(CODE_ASSISTANT_SYSTEM_PROMPT, "\n".join(prompt_parts))
        return await self._extract_code_response(messages, language)

    async def _debug_code(
        self, description: str, code: str, language: str
    ) -> dict[str, Any]:
        """Diagnose and fix bugs in code."""
        prompt_parts = [
            "The following code has a bug. Diagnose the issue and provide a fix.\n"
        ]
        if language:
            prompt_parts.append(f"Language: {language}\n")
        prompt_parts.append(f"\nCode:\n```\n{code[:6000]}\n```\n")
        if description:
            prompt_parts.append(f"\nError description: {description}\n")
        prompt_parts.append(
            "\nRespond with a JSON object:\n"
            '{"code": "<fixed code>", "language": "...", '
            '"explanation": "<what was wrong and how it was fixed>", '
            '"suggestions": [...]}'
        )

        messages = self._build_messages(CODE_ASSISTANT_SYSTEM_PROMPT, "\n".join(prompt_parts))
        return await self._extract_code_response(messages, language)

    async def _explain_code(
        self, description: str, code: str, language: str
    ) -> dict[str, Any]:
        """Explain how a piece of code works."""
        prompt_parts = ["Explain the following code in detail.\n"]
        if language:
            prompt_parts.append(f"Language: {language}\n")
        prompt_parts.append(f"\nCode:\n```\n{code[:6000]}\n```\n")
        if description:
            prompt_parts.append(f"\nSpecific question: {description}\n")
        prompt_parts.append(
            "\nRespond with a JSON object:\n"
            '{"code": "<original code>", "language": "...", '
            '"explanation": "<detailed explanation>", "suggestions": [...]}'
        )

        messages = self._build_messages(CODE_ASSISTANT_SYSTEM_PROMPT, "\n".join(prompt_parts))
        return await self._extract_code_response(messages, language)

    async def _refactor_code(
        self, description: str, code: str, language: str
    ) -> dict[str, Any]:
        """Suggest and apply refactoring improvements."""
        prompt_parts = [
            "Refactor the following code for better readability, maintainability, "
            "and performance.\n"
        ]
        if language:
            prompt_parts.append(f"Language: {language}\n")
        prompt_parts.append(f"\nCode:\n```\n{code[:6000]}\n```\n")
        if description:
            prompt_parts.append(f"\nRefactoring goals: {description}\n")
        prompt_parts.append(
            "\nRespond with a JSON object:\n"
            '{"code": "<refactored code>", "language": "...", '
            '"explanation": "<what changed and why>", "suggestions": [...]}'
        )

        messages = self._build_messages(CODE_ASSISTANT_SYSTEM_PROMPT, "\n".join(prompt_parts))
        return await self._extract_code_response(messages, language)

    async def _generate_tests(
        self, description: str, code: str, language: str
    ) -> dict[str, Any]:
        """Generate unit tests for the given code."""
        prompt_parts = ["Generate comprehensive unit tests for the following code.\n"]
        if language:
            prompt_parts.append(f"Language: {language}\n")
        prompt_parts.append(f"\nCode:\n```\n{code[:6000]}\n```\n")
        if description:
            prompt_parts.append(f"\nAdditional requirements: {description}\n")
        prompt_parts.append(
            "\nRespond with a JSON object:\n"
            '{"code": "<test code>", "language": "...", '
            '"explanation": "<testing approach>", "tests": [{"name": "...", '
            '"description": "...", "type": "unit|integration"}], "suggestions": [...]}'
        )

        messages = self._build_messages(CODE_ASSISTANT_SYSTEM_PROMPT, "\n".join(prompt_parts))
        return await self._extract_code_response(messages, language)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _extract_code_response(
        self, messages: list[dict[str, str]], default_language: str
    ) -> dict[str, Any]:
        """Call the LLM and extract the standardised code-response dict."""
        try:
            response = await self._generate_response(messages, temperature=0.3, max_tokens=4096)
            parsed = self._parse_json_response(response)
            if isinstance(parsed, dict):
                parsed.setdefault("code", "")
                parsed.setdefault("language", default_language)
                parsed.setdefault("explanation", "")
                parsed.setdefault("suggestions", [])
                parsed.setdefault("tests", [])
                return parsed
        except Exception:
            self.logger.exception("Code assistant LLM call failed")

        return {
            "code": "",
            "language": default_language,
            "explanation": "Unable to generate response.",
            "suggestions": [],
            "tests": [],
        }
