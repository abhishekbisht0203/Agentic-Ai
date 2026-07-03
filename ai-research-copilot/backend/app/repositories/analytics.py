"""Analytics repository with domain-specific query methods."""

import uuid
from typing import Any, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analytics import AnalyticsReport, Visualization
from app.repositories.base import BaseRepository


class AnalyticsReportRepository(BaseRepository[AnalyticsReport]):
    """Repository for AnalyticsReport model operations.

    Extends BaseRepository with report-specific queries such as
    listing reports by user.
    """

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(AnalyticsReport, db)

    async def get_reports_by_user(
        self, user_id: uuid.UUID, skip: int = 0, limit: int = 20
    ) -> tuple[Sequence[AnalyticsReport], int]:
        """Retrieve a paginated list of analytics reports belonging to a user.

        Args:
            user_id: The UUID of the owning user.
            skip: Number of records to skip for pagination.
            limit: Maximum number of records to return.

        Returns:
            A tuple of (list of analytics reports, total count).
        """
        return await self.get_all(
            skip=skip,
            limit=limit,
            filters={"user_id": user_id},
            order_by="created_at",
            order_desc=True,
        )


class VisualizationRepository(BaseRepository[Visualization]):
    """Repository for Visualization model operations.

    Extends BaseRepository with visualization-specific queries such as
    listing visualizations by user.
    """

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Visualization, db)

    async def get_visualizations_by_user(
        self, user_id: uuid.UUID, skip: int = 0, limit: int = 20
    ) -> tuple[Sequence[Visualization], int]:
        """Retrieve a paginated list of visualizations belonging to a user.

        Args:
            user_id: The UUID of the owning user.
            skip: Number of records to skip for pagination.
            limit: Maximum number of records to return.

        Returns:
            A tuple of (list of visualizations, total count).
        """
        return await self.get_all(
            skip=skip,
            limit=limit,
            filters={"user_id": user_id},
            order_by="created_at",
            order_desc=True,
        )
