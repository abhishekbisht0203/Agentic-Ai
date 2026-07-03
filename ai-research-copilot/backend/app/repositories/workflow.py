"""Workflow repository with domain-specific query methods."""

import uuid
from typing import Any, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workflow import Workflow
from app.repositories.base import BaseRepository


class WorkflowRepository(BaseRepository[Workflow]):
    """Repository for Workflow model operations.

    Extends BaseRepository with workflow-specific queries such as
    listing workflows by user.
    """

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Workflow, db)

    async def get_by_user(
        self, user_id: uuid.UUID, skip: int = 0, limit: int = 20
    ) -> tuple[Sequence[Workflow], int]:
        """Retrieve a paginated list of workflows belonging to a user.

        Args:
            user_id: The UUID of the owning user.
            skip: Number of records to skip for pagination.
            limit: Maximum number of records to return.

        Returns:
            A tuple of (list of workflows, total count).
        """
        return await self.get_all(
            skip=skip,
            limit=limit,
            filters={"user_id": user_id},
            order_by="created_at",
            order_desc=True,
        )
