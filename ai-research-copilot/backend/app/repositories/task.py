"""Task repository with domain-specific query methods."""

import uuid
from typing import Any, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workflow import Task, TaskStatus
from app.repositories.base import BaseRepository


class TaskRepository(BaseRepository[Task]):
    """Repository for Task model operations.

    Extends BaseRepository with task-specific queries such as
    listing tasks by user, looking up by Celery task ID,
    and retrieving pending tasks.
    """

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Task, db)

    async def get_by_user(
        self, user_id: uuid.UUID, skip: int = 0, limit: int = 20
    ) -> tuple[Sequence[Task], int]:
        """Retrieve a paginated list of tasks belonging to a user.

        Args:
            user_id: The UUID of the owning user.
            skip: Number of records to skip for pagination.
            limit: Maximum number of records to return.

        Returns:
            A tuple of (list of tasks, total count).
        """
        return await self.get_all(
            skip=skip,
            limit=limit,
            filters={"user_id": user_id},
            order_by="created_at",
            order_desc=True,
        )

    async def get_by_celery_id(
        self, celery_task_id: str
    ) -> Task | None:
        """Retrieve a task by its Celery task ID.

        Args:
            celery_task_id: The Celery async task identifier string.

        Returns:
            The matching Task instance, or None if not found.
        """
        query = select(Task).where(
            Task.celery_task_id == celery_task_id,
            Task.is_deleted == False,
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_pending_tasks(self) -> list[Task]:
        """Retrieve all pending tasks ordered by priority descending.

        Returns tasks that are waiting to be processed, sorted by
        priority (highest first) then by creation time (oldest first).

        Returns:
            A list of Task instances with status 'pending'.
        """
        query = (
            select(Task)
            .where(
                Task.status == TaskStatus.PENDING,
                Task.is_deleted == False,
            )
            .order_by(Task.priority.desc(), Task.created_at.asc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
