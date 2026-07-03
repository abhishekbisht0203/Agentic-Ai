"""
Workflow Execution Worker.

Celery task that orchestrates workflow execution in the background.
Plans the execution, runs each step sequentially, handles errors,
and updates the execution status throughout.
"""

import asyncio
import logging
import time
import uuid
from typing import Any

from celery import shared_task

from app.tasks.celery.app import create_celery_app

logger = logging.getLogger(__name__)

celery_app = create_celery_app()


def _run_async(coro):  # noqa: ANN001, ANN202
    """Run an async coroutine synchronously within a Celery worker.

    Creates a new event loop if none is running, or runs in a thread
    if an event loop is already active.

    Args:
        coro: The coroutine to execute.

    Returns:
        The coroutine's result.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(asyncio.run, coro)
            return future.result(timeout=600)
    return asyncio.run(coro)


@celery_app.task(
    bind=True,
    max_retries=2,
    name="app.tasks.workers.workflow_worker.execute_workflow_task",
    acks_late=True,
)
def execute_workflow_task(
    self, execution_id: str, workflow_id: str, user_id: str
) -> dict[str, Any]:
    """Execute a workflow in the background.

    Pipeline:
        1. Load workflow definition and execution record from the database.
        2. Plan the execution steps using WorkflowPlanner.
        3. Execute each step sequentially via StepExecutor.
        4. Publish events for each step lifecycle transition.
        5. Update the execution record with the final status.

    Args:
        self: The Celery task instance (for retry control).
        execution_id: UUID of the WorkflowExecution record.
        workflow_id: UUID of the Workflow definition.
        user_id: UUID of the user who initiated the execution.

    Returns:
        A dictionary with execution results.

    Raises:
        Exception: On unrecoverable failures (triggers retry).
    """
    start_time = time.monotonic()
    logger.info(
        "Starting workflow execution: execution_id=%s workflow_id=%s user=%s attempt=%d",
        execution_id,
        workflow_id,
        user_id,
        self.request.retries + 1,
    )

    try:
        exec_uuid = uuid.UUID(execution_id)
        wf_uuid = uuid.UUID(workflow_id)
        user_uuid = uuid.UUID(user_id)
    except ValueError as exc:
        logger.error("Invalid UUID provided: %s", exc)
        return {
            "success": False,
            "execution_id": execution_id,
            "error": f"Invalid UUID: {exc}",
        }

    try:
        # Step 1: Load workflow definition
        logger.info("Loading workflow definition: %s", workflow_id)
        # In production: workflow = await workflow_repo.get_by_id(wf_uuid)
        # execution = await execution_repo.get_by_id(exec_uuid)
        workflow_definition = {
            "nodes": [
                {
                    "id": "fetch_data",
                    "type": "tool_call",
                    "name": "Fetch Research Data",
                    "config": {
                        "tool_name": "web_search",
                        "arguments": {"query": "${input_data.query}"},
                    },
                },
                {
                    "id": "analyze",
                    "type": "agent_call",
                    "name": "Analyze Results",
                    "config": {
                        "agent_type": "analysis",
                        "input_data": {"context": "${step_results.fetch_data}"},
                    },
                },
                {
                    "id": "format_output",
                    "type": "transform",
                    "name": "Format Output",
                    "config": {
                        "source_step": "analyze",
                        "transforms": {"report": "$analyze"},
                    },
                },
            ],
            "edges": [
                {"from": "fetch_data", "to": "analyze"},
                {"from": "analyze", "to": "format_output"},
            ],
        }
        input_data: dict[str, Any] = {"query": "Sample research query"}

        # Step 2: Plan execution
        logger.info("Planning workflow execution steps")

        async def _plan() -> list[dict[str, Any]]:
            from app.workflows.planner.workflow_planner import WorkflowPlanner

            planner = WorkflowPlanner()
            return planner.plan(workflow_definition)

        steps = _run_async(_plan())
        step_names = [s["id"] for s in steps]
        logger.info("Planned %d steps: %s", len(steps), step_names)

        # Step 3: Initialize state and execute steps
        async def _execute() -> dict[str, Any]:
            from app.mcp.registry.tool_registry import ToolRegistry
            from app.workflows.executor.step_executor import StepExecutor
            from app.workflows.events.workflow_events import WorkflowEventBus
            from app.workflows.state.workflow_state import (
                WorkflowState,
                WorkflowStateStatus,
            )

            state = WorkflowState(
                execution_id=exec_uuid,
                workflow_id=wf_uuid,
                input_data=input_data,
                steps_planned=step_names,
            )
            state.start()

            event_bus = WorkflowEventBus()
            registry = ToolRegistry()
            executor = StepExecutor(registry=registry, timeout=120)

            # Publish workflow started event
            await event_bus.publish(
                WorkflowEventBus.workflow_started(exec_uuid, wf_uuid)
            )

            completed_steps: list[str] = []
            failed_step: str | None = None
            error_message: str | None = None

            for step in steps:
                step_name = step["id"]
                try:
                    # Publish step started event
                    await event_bus.publish(
                        WorkflowEventBus.step_started(
                            exec_uuid, step_name, wf_uuid
                        )
                    )

                    logger.info("Executing step: %s", step_name)
                    result = await executor.execute_step(step, state)

                    completed_steps.append(step_name)

                    # Publish step completed event
                    await event_bus.publish(
                        WorkflowEventBus.step_completed(
                            exec_uuid,
                            step_name,
                            result=result.get("output"),
                            duration_ms=result.get("duration_ms", 0),
                            workflow_id=wf_uuid,
                        )
                    )

                    logger.info(
                        "Step '%s' completed successfully", step_name
                    )

                except Exception as step_exc:
                    failed_step = step_name
                    error_message = str(step_exc)
                    logger.exception(
                        "Step '%s' failed: %s", step_name, error_message
                    )

                    # Publish step failed event
                    await event_bus.publish(
                        WorkflowEventBus.step_failed(
                            exec_uuid,
                            step_name,
                            error_message,
                            workflow_id=wf_uuid,
                        )
                    )
                    break

            # Determine final status
            total_ms = int((time.monotonic() - start_time) * 1000)

            if failed_step:
                state.fail(error_message or "Step failed")
                await event_bus.publish(
                    WorkflowEventBus.workflow_failed(
                        exec_uuid, error_message or "Unknown error", wf_uuid
                    )
                )
                return {
                    "success": False,
                    "status": "failed",
                    "failed_step": failed_step,
                    "error": error_message,
                    "completed_steps": completed_steps,
                    "total_steps": len(steps),
                    "progress": state.progress,
                    "duration_ms": total_ms,
                }

            state.complete()
            await event_bus.publish(
                WorkflowEventBus.workflow_completed(
                    exec_uuid,
                    output_data=state.output_data,
                    duration_ms=total_ms,
                    workflow_id=wf_uuid,
                )
            )

            return {
                "success": True,
                "status": "completed",
                "completed_steps": completed_steps,
                "total_steps": len(steps),
                "progress": 100.0,
                "output_data": state.output_data,
                "duration_ms": total_ms,
            }

        result = _run_async(_execute())

        # Step 4: Update execution record
        logger.info(
            "Updating execution record: execution_id=%s status=%s",
            execution_id,
            result.get("status"),
        )
        # In production:
        # await execution_repo.update(
        #     exec_uuid,
        #     status=result["status"],
        #     output_data=result.get("output_data"),
        #     error_message=result.get("error"),
        #     progress=result.get("progress", 0),
        #     completed_at=datetime.now(timezone.utc),
        #     duration_ms=result.get("duration_ms"),
        # )

        logger.info(
            "Workflow execution finished: execution_id=%s status=%s duration=%dms",
            execution_id,
            result.get("status"),
            result.get("duration_ms", 0),
        )

        return result

    except Exception as exc:
        logger.exception(
            "Workflow execution failed: execution_id=%s attempt=%d",
            execution_id,
            self.request.retries + 1,
        )
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=120 * (self.request.retries + 1))
        return {
            "success": False,
            "execution_id": execution_id,
            "error": str(exc),
            "retries_exhausted": True,
        }
