"""
Agent Execution Worker.

Celery task that executes agent tasks in the background. Loads the
agent configuration, invokes the LLM, processes tool calls, and
stores the result.
"""

import logging
import time
import uuid
from typing import Any

from celery import shared_task

from app.tasks.celery.app import create_celery_app

logger = logging.getLogger(__name__)

celery_app = create_celery_app()


def _build_system_prompt(config: dict[str, Any]) -> str:
    """Build the full system prompt from agent configuration.

    Args:
        config: Agent configuration dictionary with ``system_prompt``,
                ``tools``, and other settings.

    Returns:
        The assembled system prompt string.
    """
    parts: list[str] = []

    base_prompt = config.get("system_prompt", "")
    if base_prompt:
        parts.append(base_prompt)

    tools = config.get("tools", [])
    if tools:
        parts.append("\nAvailable tools:")
        for tool in tools:
            if isinstance(tool, dict):
                parts.append(f"- {tool.get('name', 'unknown')}: {tool.get('description', '')}")
            elif isinstance(tool, str):
                parts.append(f"- {tool}")

    parts.append(
        "\nYou are an AI assistant in the AI Research Copilot system. "
        "Provide accurate, helpful, and well-structured responses."
    )

    return "\n".join(parts)


def _process_tool_calls(
    tool_calls: list[dict[str, Any]],
    available_tools: list[str],
) -> list[dict[str, Any]]:
    """Process tool calls from the LLM response.

    In production this would invoke the MCP ToolExecutor. Here we
    return structured stubs for the worker to process.

    Args:
        tool_calls: List of tool call dictionaries from the LLM.
        available_tools: List of available tool names.

    Returns:
        A list of processed tool call results.
    """
    results: list[dict[str, Any]] = []
    for call in tool_calls:
        tool_name = call.get("function", {}).get("name", call.get("name", ""))
        arguments = call.get("function", {}).get("arguments", call.get("arguments", {}))

        if tool_name not in available_tools:
            results.append(
                {
                    "tool_name": tool_name,
                    "success": False,
                    "error": f"Tool '{tool_name}' is not available",
                }
            )
            continue

        # In production: result = await tool_executor.execute_with_timeout(tool_name, **arguments)
        results.append(
            {
                "tool_name": tool_name,
                "success": True,
                "result": f"Simulated result for tool '{tool_name}'",
                "arguments": arguments,
            }
        )

    return results


@celery_app.task(
    bind=True,
    max_retries=3,
    name="app.tasks.workers.agent_worker.execute_agent_task",
    acks_late=True,
)
def execute_agent_task(self, task_id: str, user_id: str) -> dict[str, Any]:
    """Execute an agent task in the background.

    Pipeline:
        1. Load task metadata and agent configuration from the database.
        2. Build the system prompt and conversation context.
        3. Call the LLM with the prepared messages.
        4. Process any tool calls requested by the LLM.
        5. Store the final response and update task status.

    Args:
        self: The Celery task instance (for retry control).
        task_id: UUID of the Task record to execute.
        user_id: UUID of the user who initiated the task.

    Returns:
        A dictionary with execution results.

    Raises:
        Exception: On unrecoverable failures (triggers retry).
    """
    start_time = time.monotonic()
    logger.info(
        "Starting agent task execution: task_id=%s user=%s attempt=%d",
        task_id,
        user_id,
        self.request.retries + 1,
    )

    try:
        task_uuid = uuid.UUID(task_id)
        user_uuid = uuid.UUID(user_id)
    except ValueError as exc:
        logger.error("Invalid UUID provided: %s", exc)
        return {
            "success": False,
            "task_id": task_id,
            "error": f"Invalid UUID: {exc}",
        }

    try:
        # Step 1: Load task and agent config
        logger.info("Loading task metadata: %s", task_id)
        # In production: task = await task_repo.get_by_id(task_uuid)
        task_data = {
            "id": task_id,
            "user_id": user_id,
            "task_type": "agent",
            "input_data": {
                "agent_type": "research",
                "input_data": {"query": "Sample research query"},
                "model": "gpt-4o",
                "system_prompt": "You are a research assistant.",
                "temperature": 0.7,
                "max_tokens": 4096,
                "tools": ["calculator", "web_search"],
            },
        }

        input_data = task_data.get("input_data", {})
        agent_type = input_data.get("agent_type", "general")
        llm_input = input_data.get("input_data", {})
        model = input_data.get("model", "gpt-4o")
        system_prompt = input_data.get("system_prompt", "")
        temperature = input_data.get("temperature", 0.7)
        max_tokens = input_data.get("max_tokens", 4096)
        tools = input_data.get("tools", [])

        logger.info(
            "Agent config loaded: type=%s model=%s tools=%d",
            agent_type,
            model,
            len(tools),
        )

        # Step 2: Build messages
        logger.info("Building conversation messages")
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        user_query = llm_input.get("query", llm_input.get("message", ""))
        if user_query:
            messages.append({"role": "user", "content": str(user_query)})

        # Step 3: Call LLM
        logger.info("Calling LLM: model=%s temperature=%.1f", model, temperature)
        # In production:
        # from app.llms.factory import LLMFactory
        # llm = LLMFactory.create(provider=model)
        # response = await llm.chat(messages=messages, temperature=temperature, max_tokens=max_tokens)
        response_content = (
            f"Agent response for '{agent_type}' task using model '{model}'. "
            f"This is a simulated response. In production, this would contain "
            f"the actual LLM output for query: {user_query}"
        )

        # Step 4: Process tool calls (if any)
        tool_results: list[dict[str, Any]] = []
        if tools:
            logger.info("Processing tool calls")
            tool_results = _process_tool_calls([], tools)

        # Step 5: Store result
        logger.info("Storing agent task result")
        duration_ms = int((time.monotonic() - start_time) * 1000)

        # In production:
        # await task_repo.update(task_uuid, status="completed", output_data={...})

        logger.info(
            "Agent task completed: task_id=%s duration=%dms",
            task_id,
            duration_ms,
        )

        return {
            "success": True,
            "task_id": task_id,
            "user_id": user_id,
            "agent_type": agent_type,
            "model": model,
            "response": response_content,
            "tool_results": tool_results,
            "tokens_used": len(response_content.split()),
            "duration_ms": duration_ms,
            "status": "completed",
        }

    except Exception as exc:
        logger.exception(
            "Agent task failed: task_id=%s attempt=%d",
            task_id,
            self.request.retries + 1,
        )
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
        return {
            "success": False,
            "task_id": task_id,
            "error": str(exc),
            "retries_exhausted": True,
        }
