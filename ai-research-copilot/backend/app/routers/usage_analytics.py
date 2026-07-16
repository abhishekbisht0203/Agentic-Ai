"""Deep analytics endpoints for token usage, costs, model performance, storage."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.dependencies.auth import get_current_user_from_token, get_optional_user
from app.models.user import User
from app.services.usage_tracking_service import UsageTrackingService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/usage/tokens")
async def get_token_usage(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    service = UsageTrackingService(db)
    user_id = current_user.id if current_user and current_user.id else None
    summary = await service.get_usage_summary(user_id, days)
    trend = await service.get_token_trend(user_id, days)
    return {"summary": summary, "trend": trend}


@router.get("/usage/costs")
async def get_cost_analytics(
    current_user: User = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    service = UsageTrackingService(db)
    user_id = current_user.id if current_user and current_user.id else None
    breakdown = await service.get_cost_breakdown(user_id)
    total = sum(b["cost"] for b in breakdown)
    return {"breakdown": breakdown, "total_cost": round(total, 6)}


@router.get("/usage/models")
async def get_model_performance(
    current_user: User = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    service = UsageTrackingService(db)
    user_id = current_user.id if current_user and current_user.id else None
    models = await service.get_model_performance(user_id)
    return {"models": models}


@router.get("/usage/errors")
async def get_error_analytics(
    current_user: User = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    service = UsageTrackingService(db)
    user_id = current_user.id if current_user and current_user.id else None
    return await service.get_error_rate(user_id)


@router.get("/usage/dashboard")
async def get_dashboard_usage(
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    service = UsageTrackingService(db)
    return await service.get_dashboard_stats(current_user.id)


@router.get("/usage/storage")
async def get_storage_usage(
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    service = UsageTrackingService(db)
    return await service.get_storage_stats(current_user.id)
