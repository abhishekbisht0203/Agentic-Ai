"""Task management service for background job tracking."""

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.models.workflow import Task, TaskStatus
from app.repositories.task import TaskRepository
from app.schemas.task import TaskList, TaskResponse

logger = logging.getLogger(__name__)


class TaskService:
    """Service for background task lifecycle management."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.task_repo = TaskRepository(db)

    async def create_task(
        self,
        user_id: uuid.UUID,
        task_type: str,
        input_data: dict | None = None,
        priority: int = 0,
    ) -> TaskResponse:
        """Create a new background task in pending state.

        Args:
            user_id: ID of the requesting user.
            task_type: Category of the task (e.g. 'document_processing').
            input_data: Optional payload describing the work to be done.
            priority: Numeric priority (higher = more urgent).

        Raises:
            ValidationError: If task_type is empty.

        Returns:
            The newly created task as a response schema.
        """
        task_type = task_type.strip()
        if not task_type:
            raise ValidationError(message="Task type cannot be empty")

        task = await self.task_repo.create(
            user_id=user_id,
            task_type=task_type,
            status=TaskStatus.PENDING,
            priority=priority,
            input_data=input_data,
        )

        logger.info(
            "Task created: id=%s type=%s user=%s priority=%s",
            task.id,
            task.task_type,
            user_id,
            task.priority,
        )
        return TaskResponse.model_validate(task)

    async def get_task(
        self, task_id: uuid.UUID, user_id: uuid.UUID
    ) -> TaskResponse:
        """Retrieve a single task by ID with ownership check.

        Args:
            task_id: UUID of the task.
            user_id: UUID of the requesting user.

        Raises:
            NotFoundError: If the task does not exist or belongs to another user.

        Returns:
            The task as a response schema.
        """
        task = await self._get_owned_task(task_id, user_id)
        return TaskResponse.model_validate(task)

    async def list_tasks(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> TaskList:
        """Return a paginated list of the user's tasks.

        Tasks are returned in reverse chronological order (newest first).

        Args:
            user_id: UUID of the owning user.
            page: 1-indexed page number.
            page_size: Number of items per page (max 100).

        Returns:
            Paginated task list with total count.
        """
        page_size = min(page_size, 100)
        skip = (page - 1) * page_size
        items, total = await self.task_repo.get_by_user(user_id, skip, page_size)
        return TaskList(
            items=[TaskResponse.model_validate(t) for t in items],
            total=total,
        )

    async def cancel_task(
        self, task_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        """Cancel a pending or running task.

        Only tasks in 'pending' or 'running' status can be cancelled.
        Tasks that have already completed, failed, or been cancelled are
        rejected with a validation error.

        Args:
            task_id: UUID of the task.
            user_id: UUID of the owning user.

        Raises:
            NotFoundError: If the task does not exist or belongs to another user.
            ValidationError: If the task is not in a cancellable state.
        """
        task = await self._get_owned_task(task_id, user_id)

        if task.status not in (TaskStatus.PENDING, TaskStatus.RUNNING):
            raise ValidationError(
                message=f"Cannot cancel task in '{task.status}' status",
                details={"task_id": str(task_id), "current_status": task.status},
            )

        await self.task_repo.update(
            task_id,
            status=TaskStatus.CANCELLED,
            completed_at=datetime.now(timezone.utc),
        )

        logger.info(
            "Task cancelled: id=%s user=%s previous_status=%s",
            task_id,
            user_id,
            task.status,
        )

    async def update_task_status(
        self,
        task_id: uuid.UUID,
        status: str,
        output_data: dict | None = None,
        error_message: str | None = None,
    ) -> TaskResponse:
        """Update a task's status and optional output/error data.

        Intended for internal use by background workers or Celery callbacks.
        Performs a transition-aware update that sets appropriate timestamps:

        - Sets ``started_at`` when moving to 'running'.
        - Sets ``completed_at`` when moving to a terminal state
          ('completed', 'failed', or 'cancelled').
        - Increments ``retry_count`` when moving to 'retry'.

        Args:
            task_id: UUID of the task to update.
            status: New status value (must be a valid TaskStatus).
            output_data: Optional result payload (used on completion).
            error_message: Optional error description (used on failure).

        Raises:
            NotFoundError: If the task does not exist.
            ValidationError: If the status value is invalid.

        Returns:
            The updated task as a response schema.
        """
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            raise NotFoundError(
                message="Task not found",
                details={"task_id": str(task_id)},
            )

        valid_statuses = {s.value for s in TaskStatus}
        if status not in valid_statuses:
            raise ValidationError(
                message=f"Invalid task status: '{status}'",
                details={"valid_statuses": sorted(valid_statuses)},
            )

        update_fields: dict = {"status": status}
        now = datetime.now(timezone.utc)

        if status == TaskStatus.RUNNING:
            update_fields["started_at"] = now
        elif status in (
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        ):
            update_fields["completed_at"] = now
        elif status == TaskStatus.RETRY:
            update_fields["retry_count"] = task.retry_count + 1

        if output_data is not None:
            update_fields["output_data"] = output_data
        if error_message is not None:
            update_fields["error_message"] = error_message

        updated = await self.task_repo.update(task_id, **update_fields)

        logger.info(
            "Task status updated: id=%s %s -> %s",
            task_id,
            task.status,
            status,
        )
        return TaskResponse.model_validate(updated)

    async def get_pending_tasks(self) -> list[TaskResponse]:
        """Retrieve all pending tasks ordered by priority (highest first).

        Intended for the task scheduler or worker polling loop.

        Returns:
            List of pending tasks as response schemas.
        """
        tasks = await self.task_repo.get_pending_tasks()
        return [TaskResponse.model_validate(t) for t in tasks]

    # ── Internal helpers ─────────────────────────────────────────────────

    async def _get_owned_task(
        self, task_id: uuid.UUID, user_id: uuid.UUID
    ) -> Task:
        """Fetch a task and verify ownership.

        Raises:
            NotFoundError: If the task is missing or belongs to another user.
        """
        task = await self.task_repo.get_by_id(task_id)
        if not task or task.user_id != user_id:
            raise NotFoundError(message="Task not found")
        return task
