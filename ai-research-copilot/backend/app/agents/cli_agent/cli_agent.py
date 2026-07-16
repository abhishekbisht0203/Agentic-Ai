
import json
import logging
import os
import sys
from typing import Any

from app.agents.base.agent import BaseAgent
from app.llms.providers.base import BaseLLMProvider

logger = logging.getLogger(__name__)

CLI_SYSTEM_PROMPT = (
    "You are ARC (AI Research Copilot) operating as a terminal coding agent. "
    "You have full access to the codebase and can execute commands.\n\n"
    "CAPABILITIES:\n"
    "- Read, write, and edit files (use edit_file for precise changes)\n"
    "- Execute shell commands (test, lint, build, etc.)\n"
    "- Search files by glob pattern and content with regex\n"
    "- Run git operations (status, diff, log, add, commit, push, pull, branch)\n"
    "- List directory contents\n\n"
    "RULES:\n"
    "1. Always read a file before editing it\n"
    "2. For edits, use edit_file with exact old_string matching (include context)\n"
    "3. Run tests/lint/typecheck after making changes\n"
    "4. Never make assumptions about file content you haven't read\n"
    "5. Respond in this JSON format:\n"
    '{"thought": "<your reasoning>", "tool_calls": [{"name": "<tool>", "arguments": {...}}], '
    '"response": "<message to user>", "done": false}\n'
    "6. Set done=true when the task is complete\n"
    "7. Available tools: edit_file, edit_file_replace_all, read_file, read_file_range, "
    "write_file, execute_command, glob_search, grep_search, git_operations, "
    "list_directory, calculator, web_search\n\n"
    "IMPORTANT: You are an autonomous coding agent. When asked to implement something, "
    "you should: plan, read relevant files, implement changes, and verify."
)


class CLIAgent(BaseAgent):
    """Coding agent designed for terminal/CLI operation.

    Extends BaseAgent with tool-calling capabilities for file operations,
    shell commands, and codebase navigation.
    """

    agent_type: str = "cli_agent"

    def __init__(self, llm_provider: BaseLLMProvider, config: dict[str, Any] | None = None) -> None:
        super().__init__(llm_provider, config)
        self._conversation_history: list[dict[str, str]] = []

    async def execute(
        self,
        input_data: dict[str, Any],
        conversation_id: Any = None,
    ) -> dict[str, Any]:
        message = input_data.get("message", "")
        task_type = input_data.get("task_type", "chat")

        self.logger.info("CLI agent processing task_type=%s", task_type)

        if task_type == "plan_only":
            return await self._plan_task(message)
        return await self._execute_task(message)

    async def _plan_task(self, message: str) -> dict[str, Any]:
        prompt = (
            f"Analyse this request and create a step-by-step plan.\n\n"
            f"Request: {message}\n\n"
            "Respond with a JSON object:\n"
            '{"plan_title": "<title>", "steps": [{"step": 1, "action": "<what to do>", '
            '"expected_outcome": "<result>"}], "estimated_complexity": "low|medium|high"}'
        )
        messages = self._build_messages(CLI_SYSTEM_PROMPT, prompt)
        try:
            response = await self._generate_response(messages, temperature=0.3, max_tokens=2048)
            parsed = self._parse_json_response(response)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            self.logger.exception("Plan generation failed")
        return {"plan_title": message[:100], "steps": [], "estimated_complexity": "medium"}

    async def _execute_task(self, message: str) -> dict[str, Any]:
        prompt = (
            f"Task: {message}\n\n"
            "First read any relevant files to understand the codebase, then implement "
            "the changes step by step. Use tool_calls to interact with files and shell."
        )
        messages = self._build_messages(CLI_SYSTEM_PROMPT, prompt)
        try:
            response = await self._generate_response(messages, temperature=0.3, max_tokens=4096)
            parsed = self._parse_json_response(response)
            if isinstance(parsed, dict):
                return parsed
            return {"thought": "", "tool_calls": [], "response": response.content, "done": True}
        except Exception as exc:
            self.logger.exception("Task execution failed")
            return {"thought": "", "tool_calls": [], "response": f"Error: {exc}", "done": True}

    async def chat(self, message: str) -> dict[str, Any]:
        """Single-turn chat for CLI interaction with conversation history."""
        self._conversation_history.append({"role": "user", "content": message})

        prompt = message + "\n\nRespond with a JSON object with 'response' field."
        messages = self._build_messages(CLI_SYSTEM_PROMPT, prompt, include_history=True)

        try:
            response = await self._generate_response(messages, temperature=0.3, max_tokens=4096)
            parsed = self._parse_json_response(response)
            if isinstance(parsed, dict) and "response" in parsed:
                result = parsed
            else:
                result = {"response": response.content}
        except Exception as exc:
            result = {"response": f"Error: {exc}"}

        self._conversation_history.append({"role": "assistant", "content": json.dumps(result)})
        return result

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base["cli_history_length"] = len(self._conversation_history)
        return base
