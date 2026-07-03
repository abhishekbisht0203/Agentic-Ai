"""Analytics service for reports, visualizations, user activity, and summaries."""

import logging
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.models.analytics import AnalyticsReport, UserActivity, Visualization
from app.repositories.analytics import (
    AnalyticsReportRepository,
    VisualizationRepository,
)
from app.schemas.analytics import (
    AnalyticsReportCreate,
    AnalyticsReportList,
    AnalyticsReportResponse,
    AnalyticsSummary,
    UserActivityList,
    UserActivityResponse,
    VisualizationCreate,
    VisualizationList,
    VisualizationResponse,
)

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for analytics reports, visualizations, and activity tracking."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.report_repo = AnalyticsReportRepository(db)
        self.viz_repo = VisualizationRepository(db)

    # ── Reports ──────────────────────────────────────────────────────────

    async def create_report(
        self, user_id: uuid.UUID, data: AnalyticsReportCreate
    ) -> AnalyticsReportResponse:
        """Create a new analytics report.

        Args:
            user_id: ID of the requesting user.
            data: Report creation payload.

        Returns:
            The newly created report as a response schema.
        """
        report = await self.report_repo.create(
            user_id=user_id,
            name=data.name.strip(),
            report_type=data.report_type.strip(),
            status="pending",
            input_config=data.input_config,
            data_source_type=data.data_source_type,
            data_source_id=data.data_source_id,
        )

        logger.info(
            "Report created: id=%s user=%s type=%s",
            report.id,
            user_id,
            report.report_type,
        )
        return AnalyticsReportResponse.model_validate(report)

    async def get_report(
        self, report_id: uuid.UUID, user_id: uuid.UUID
    ) -> AnalyticsReportResponse:
        """Retrieve a single analytics report by ID with ownership check.

        Args:
            report_id: UUID of the report.
            user_id: UUID of the requesting user.

        Raises:
            NotFoundError: If the report does not exist or belongs to another user.

        Returns:
            The report as a response schema.
        """
        report = await self._get_owned_report(report_id, user_id)
        return AnalyticsReportResponse.model_validate(report)

    async def list_reports(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> AnalyticsReportList:
        """Return a paginated list of the user's analytics reports.

        Args:
            user_id: UUID of the owning user.
            page: 1-indexed page number.
            page_size: Number of items per page (max 100).

        Returns:
            Paginated report list with total count.
        """
        page_size = min(page_size, 100)
        skip = (page - 1) * page_size
        items, total = await self.report_repo.get_reports_by_user(
            user_id, skip, page_size
        )
        return AnalyticsReportList(
            items=[AnalyticsReportResponse.model_validate(r) for r in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def delete_report(
        self, report_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        """Soft-delete an analytics report.

        Args:
            report_id: UUID of the report.
            user_id: UUID of the owning user.

        Raises:
            NotFoundError: If the report does not exist or belongs to another user.
        """
        await self._get_owned_report(report_id, user_id)
        await self.report_repo.delete(report_id)
        logger.info("Report deleted: id=%s user=%s", report_id, user_id)

    # ── Visualizations ───────────────────────────────────────────────────

    async def create_visualization(
        self, user_id: uuid.UUID, data: VisualizationCreate
    ) -> VisualizationResponse:
        """Create a new visualization.

        Validates that the linked report (if any) exists and belongs to the user.

        Args:
            user_id: ID of the requesting user.
            data: Visualization creation payload.

        Raises:
            NotFoundError: If the linked report does not exist or belongs to another user.

        Returns:
            The newly created visualization as a response schema.
        """
        if data.report_id is not None:
            report = await self._get_owned_report(data.report_id, user_id)

        viz = await self.viz_repo.create(
            user_id=user_id,
            report_id=data.report_id,
            name=data.name.strip(),
            chart_type=data.chart_type.strip(),
            config=data.config,
        )

        logger.info(
            "Visualization created: id=%s user=%s chart_type=%s",
            viz.id,
            user_id,
            viz.chart_type,
        )
        return VisualizationResponse.model_validate(viz)

    async def get_visualization(
        self, viz_id: uuid.UUID, user_id: uuid.UUID
    ) -> VisualizationResponse:
        """Retrieve a single visualization by ID with ownership check.

        Args:
            viz_id: UUID of the visualization.
            user_id: UUID of the requesting user.

        Raises:
            NotFoundError: If the visualization does not exist or belongs to another user.

        Returns:
            The visualization as a response schema.
        """
        viz = await self._get_owned_visualization(viz_id, user_id)
        return VisualizationResponse.model_validate(viz)

    async def list_visualizations(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> VisualizationList:
        """Return a paginated list of the user's visualizations.

        Args:
            user_id: UUID of the owning user.
            page: 1-indexed page number.
            page_size: Number of items per page (max 100).

        Returns:
            Paginated visualization list with total count.
        """
        page_size = min(page_size, 100)
        skip = (page - 1) * page_size
        items, total = await self.viz_repo.get_visualizations_by_user(
            user_id, skip, page_size
        )
        return VisualizationList(
            items=[VisualizationResponse.model_validate(v) for v in items],
            total=total,
        )

    async def delete_visualization(
        self, viz_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        """Soft-delete a visualization.

        Args:
            viz_id: UUID of the visualization.
            user_id: UUID of the owning user.

        Raises:
            NotFoundError: If the visualization does not exist or belongs to another user.
        """
        await self._get_owned_visualization(viz_id, user_id)
        await self.viz_repo.delete(viz_id)
        logger.info("Visualization deleted: id=%s user=%s", viz_id, user_id)

    # ── User Activity ────────────────────────────────────────────────────

    async def get_user_activity(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> UserActivityList:
        """Return a paginated list of the user's activity records.

        Activities are returned in reverse chronological order (newest first).

        Args:
            user_id: UUID of the owning user.
            page: 1-indexed page number.
            page_size: Number of items per page (max 100).

        Returns:
            Paginated activity list with total count.
        """
        page_size = min(page_size, 100)
        skip = (page - 1) * page_size

        items, total = await self._get_activities_page(user_id, skip, page_size)

        return UserActivityList(
            items=[
                UserActivityResponse.model_validate(a) for a in items
            ],
            total=total,
        )

    # ── Summary ──────────────────────────────────────────────────────────

    async def get_summary(self, user_id: uuid.UUID) -> AnalyticsSummary:
        """Aggregate analytics summary for the user's dashboard.

        Computes report and visualization counts, activity totals, report
        distribution by type, and the 10 most recent activities.

        Args:
            user_id: UUID of the owning user.

        Returns:
            Aggregated summary data.
        """
        total_reports = await self.report_repo.count(filters={"user_id": user_id})
        total_viz = await self.viz_repo.count(filters={"user_id": user_id})
        total_activities = await self._count_activities(user_id)

        reports_by_type = await self._count_reports_by_type(user_id)

        recent = await self._get_recent_activities(user_id, limit=10)
        recent_activities = [
            UserActivityResponse.model_validate(a).model_dump(mode="json")
            for a in recent
        ]

        return AnalyticsSummary(
            total_reports=total_reports,
            total_visualizations=total_viz,
            activity_count=total_activities,
            reports_by_type=reports_by_type,
            recent_activities=recent_activities,
        )

    # ── Internal helpers ─────────────────────────────────────────────────

    async def _get_owned_report(
        self, report_id: uuid.UUID, user_id: uuid.UUID
    ) -> AnalyticsReport:
        """Fetch a report and verify ownership."""
        report = await self.report_repo.get_by_id(report_id)
        if not report or report.user_id != user_id:
            raise NotFoundError(message="Analytics report not found")
        return report

    async def _get_owned_visualization(
        self, viz_id: uuid.UUID, user_id: uuid.UUID
    ) -> Visualization:
        """Fetch a visualization and verify ownership."""
        viz = await self.viz_repo.get_by_id(viz_id)
        if not viz or viz.user_id != user_id:
            raise NotFoundError(message="Visualization not found")
        return viz

    async def _get_activities_page(
        self, user_id: uuid.UUID, skip: int, limit: int
    ) -> tuple[list[UserActivity], int]:
        """Retrieve a paginated slice of user activities.

        Returns:
            Tuple of (list of UserActivity records, total count).
        """
        base_filter = UserActivity.user_id == user_id

        count_q = (
            select(func.count())
            .select_from(UserActivity)
            .where(base_filter)
        )
        count_result = await self.db.execute(count_q)
        total = count_result.scalar() or 0

        items_q = (
            select(UserActivity)
            .where(base_filter)
            .order_by(UserActivity.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(items_q)
        items = list(result.scalars().all())
        return items, total

    async def _count_activities(self, user_id: uuid.UUID) -> int:
        """Count total activity records for a user."""
        query = (
            select(func.count())
            .select_from(UserActivity)
            .where(UserActivity.user_id == user_id)
        )
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def _count_reports_by_type(self, user_id: uuid.UUID) -> dict[str, int]:
        """Count reports grouped by report_type for a user."""
        query = (
            select(
                AnalyticsReport.report_type,
                func.count(AnalyticsReport.id),
            )
            .where(
                AnalyticsReport.user_id == user_id,
                AnalyticsReport.is_deleted == False,
            )
            .group_by(AnalyticsReport.report_type)
        )
        result = await self.db.execute(query)
        return {row[0]: row[1] for row in result.all()}

    async def _get_recent_activities(
        self, user_id: uuid.UUID, limit: int = 10
    ) -> list[UserActivity]:
        """Fetch the most recent activity records for a user."""
        query = (
            select(UserActivity)
            .where(UserActivity.user_id == user_id)
            .order_by(UserActivity.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
