"""Analytics router for reports, visualizations, activity, and summary endpoints."""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.dependencies.auth import get_current_user_from_token
from app.models.user import User
from app.schemas.analytics import (
    AnalyticsReportCreate,
    AnalyticsReportList,
    AnalyticsReportResponse,
    AnalyticsSummary,
    UserActivityList,
    VisualizationCreate,
    VisualizationList,
    VisualizationResponse,
)
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.post("/reports", response_model=AnalyticsReportResponse, status_code=201)
async def create_report(
    data: AnalyticsReportCreate,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db_session),
) -> AnalyticsReportResponse:
    """Create a new analytics report."""
    service = AnalyticsService(db)
    return await service.create_report(current_user.id, data)


@router.get("/reports", response_model=AnalyticsReportList)
async def list_reports(
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db_session),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> AnalyticsReportList:
    """List analytics reports for the current user with pagination."""
    service = AnalyticsService(db)
    return await service.list_reports(current_user.id, page, page_size)


@router.get("/reports/{report_id}", response_model=AnalyticsReportResponse)
async def get_report(
    report_id: uuid.UUID,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db_session),
) -> AnalyticsReportResponse:
    """Get a single analytics report by ID."""
    service = AnalyticsService(db)
    return await service.get_report(report_id, current_user.id)


@router.delete("/reports/{report_id}", status_code=204)
async def delete_report(
    report_id: uuid.UUID,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """Delete an analytics report."""
    service = AnalyticsService(db)
    await service.delete_report(report_id, current_user.id)


@router.post("/visualizations", response_model=VisualizationResponse, status_code=201)
async def create_visualization(
    data: VisualizationCreate,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db_session),
) -> VisualizationResponse:
    """Create a new visualization."""
    service = AnalyticsService(db)
    return await service.create_visualization(current_user.id, data)


@router.get("/visualizations", response_model=VisualizationList)
async def list_visualizations(
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db_session),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> VisualizationList:
    """List visualizations for the current user with pagination."""
    service = AnalyticsService(db)
    return await service.list_visualizations(current_user.id, page, page_size)


@router.get("/visualizations/{viz_id}", response_model=VisualizationResponse)
async def get_visualization(
    viz_id: uuid.UUID,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db_session),
) -> VisualizationResponse:
    """Get a single visualization by ID."""
    service = AnalyticsService(db)
    return await service.get_visualization(viz_id, current_user.id)


@router.delete("/visualizations/{viz_id}", status_code=204)
async def delete_visualization(
    viz_id: uuid.UUID,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """Delete a visualization."""
    service = AnalyticsService(db)
    await service.delete_visualization(viz_id, current_user.id)


@router.get("/activity", response_model=UserActivityList)
async def get_user_activity(
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db_session),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> UserActivityList:
    """Get paginated user activity records."""
    service = AnalyticsService(db)
    return await service.get_user_activity(current_user.id, page, page_size)


@router.get("/summary", response_model=AnalyticsSummary)
async def get_analytics_summary(
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db_session),
) -> AnalyticsSummary:
    """Get aggregated analytics summary for the current user."""
    service = AnalyticsService(db)
    return await service.get_summary(current_user.id)
