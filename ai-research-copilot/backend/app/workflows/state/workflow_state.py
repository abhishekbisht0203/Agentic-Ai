"""
Workflow State management.

Defines the status lifecycle and runtime state object for a single
workflow execution. The state is passed through every step executor
and planner to maintain context across the execution graph.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class WorkflowStateStatus(str, Enum):
    """Lifecycle statuses for a workflow execution."""

    PENDING = "pending"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

    @property
    def is_terminal(self) -> bool:
        """Return True if the status represents a final state."""
        return self in (
            WorkflowStateStatus.COMPLETED,
            WorkflowStateStatus.FAILED,
            WorkflowStateStatus.CANCELLED,
        )

    @property
    def is_active(self) -> bool:
        """Return True if the status represents an in-progress execution."""
        return self in (
            WorkflowStateStatus.PENDING,
            WorkflowStateStatus.RUNNING,
            WorkflowStateStatus.WAITING_APPROVAL,
        )


@dataclass
class WorkflowState:
    """Runtime state for a workflow execution.

    Mutable state object threaded through every step of a workflow
    execution. Planners and executors read from and write to this
    object to coordinate progress, share data between steps, and
    track overall execution status.

    Attributes:
        execution_id: Unique identifier for this execution run.
        workflow_id: Reference to the workflow definition.
        status: Current lifecycle status.
        current_step: Name of the step currently being executed.
        input_data: Data provided when the execution was initiated.
        output_data: Aggregated output produced by completed steps.
        step_results: Mapping of step name to its individual result.
        progress: Overall progress percentage (0.0 – 100.0).
        error: Error message if the execution has failed.
        started_at: Timestamp when execution transitioned to RUNNING.
        completed_at: Timestamp when execution reached a terminal state.
        metadata: Free-form metadata for logging / observability.
        retry_count: Number of times the current step has been retried.
        steps_planned: Ordered list of step names from the planner.
    """

    execution_id: uuid.UUID
    workflow_id: uuid.UUID
    status: WorkflowStateStatus = WorkflowStateStatus.PENDING
    current_step: str | None = None
    input_data: dict[str, Any] = field(default_factory=dict)
    output_data: dict[str, Any] = field(default_factory=dict)
    step_results: dict[str, Any] = field(default_factory=dict)
    progress: float = 0.0
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    steps_planned: list[str] = field(default_factory=list)

    # ------------------------------------------------------------------
    # State transitions
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Transition to RUNNING and record the start timestamp."""
        if not self.status.is_active:
            raise RuntimeError(
                f"Cannot start workflow in status '{self.status.value}'"
            )
        self.status = WorkflowStateStatus.RUNNING
        self.started_at = datetime.now(timezone.utc)

    def mark_step_running(self, step_name: str) -> None:
        """Record that a specific step has started.

        Args:
            step_name: The name of the step now executing.
        """
        self.current_step = step_name
        self.retry_count = 0

    def complete_step(self, step_name: str, result: Any) -> None:
        """Record the successful completion of a step.

        Args:
            step_name: The name of the completed step.
            result: The result produced by the step.
        """
        self.step_results[step_name] = result
        self.output_data[step_name] = result
        self._update_progress()

    def fail(self, error: str) -> None:
        """Transition to FAILED status.

        Args:
            error: A human-readable description of the failure.
        """
        self.status = WorkflowStateStatus.FAILED
        self.error = error
        self.completed_at = datetime.now(timezone.utc)

    def complete(self) -> None:
        """Transition to COMPLETED status."""
        self.status = WorkflowStateStatus.COMPLETED
        self.progress = 100.0
        self.completed_at = datetime.now(timezone.utc)

    def cancel(self) -> None:
        """Transition to CANCELLED status."""
        if self.status.is_terminal:
            raise RuntimeError(
                f"Cannot cancel workflow in terminal status '{self.status.value}'"
            )
        self.status = WorkflowStateStatus.CANCELLED
        self.completed_at = datetime.now(timezone.utc)

    def wait_for_approval(self) -> None:
        """Transition to WAITING_APPROVAL status."""
        if not self.status.is_active and self.status != WorkflowStateStatus.RUNNING:
            raise RuntimeError(
                f"Cannot wait for approval in status '{self.status.value}'"
            )
        self.status = WorkflowStateStatus.WAITING_APPROVAL

    def resume_after_approval(self) -> None:
        """Resume from WAITING_APPROVAL back to RUNNING."""
        if self.status != WorkflowStateStatus.WAITING_APPROVAL:
            raise RuntimeError(
                f"Cannot resume from status '{self.status.value}'"
            )
        self.status = WorkflowStateStatus.RUNNING

    def increment_retry(self) -> int:
        """Increment the retry counter and return the new count.

        Returns:
            The updated retry count.
        """
        self.retry_count += 1
        return self.retry_count

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _update_progress(self) -> None:
        """Recalculate progress based on completed steps vs planned steps."""
        if not self.steps_planned:
            self.progress = 0.0
            return
        completed = len(self.step_results)
        total = len(self.steps_planned)
        self.progress = round((completed / total) * 100, 2)

    def get_step_result(self, step_name: str) -> Any | None:
        """Retrieve the result of a previously completed step.

        Args:
            step_name: The step name to look up.

        Returns:
            The step's result, or None if not yet completed.
        """
        return self.step_results.get(step_name)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the state to a JSON-compatible dictionary.

        Returns:
            A dictionary representation suitable for persistence or logging.
        """
        return {
            "execution_id": str(self.execution_id),
            "workflow_id": str(self.workflow_id),
            "status": self.status.value,
            "current_step": self.current_step,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "step_results": self.step_results,
            "progress": self.progress,
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "metadata": self.metadata,
            "retry_count": self.retry_count,
            "steps_planned": self.steps_planned,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkflowState":
        """Deserialize a state from a dictionary.

        Args:
            data: Dictionary previously produced by ``to_dict``.

        Returns:
            A reconstructed WorkflowState instance.
        """
        return cls(
            execution_id=uuid.UUID(data["execution_id"]),
            workflow_id=uuid.UUID(data["workflow_id"]),
            status=WorkflowStateStatus(data["status"]),
            current_step=data.get("current_step"),
            input_data=data.get("input_data", {}),
            output_data=data.get("output_data", {}),
            step_results=data.get("step_results", {}),
            progress=data.get("progress", 0.0),
            error=data.get("error"),
            started_at=(
                datetime.fromisoformat(data["started_at"])
                if data.get("started_at")
                else None
            ),
            completed_at=(
                datetime.fromisoformat(data["completed_at"])
                if data.get("completed_at")
                else None
            ),
            metadata=data.get("metadata", {}),
            retry_count=data.get("retry_count", 0),
            steps_planned=data.get("steps_planned", []),
        )
