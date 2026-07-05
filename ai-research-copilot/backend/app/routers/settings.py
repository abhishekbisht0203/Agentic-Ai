"""Settings router for application info and user preferences."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database.session import get_db_session
from app.dependencies.auth import get_current_user_from_token
from app.models.user import User
from app.schemas.memory import UserPreferenceResponse, UserPreferenceUpdate
from app.services.memory_service import MemoryService

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("/preferences")
async def get_preferences(
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db_session),
) -> list[UserPreferenceResponse]:
    """Get all preferences for the current user."""
    service = MemoryService(db)
    return await service.get_preferences(current_user.id)


@router.put("/preferences", response_model=UserPreferenceResponse)
async def update_preference(
    data: UserPreferenceUpdate,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db_session),
) -> UserPreferenceResponse:
    """Create or update a user preference."""
    service = MemoryService(db)
    return await service.update_preference(current_user.id, data)


@router.get("/info")
async def get_application_info() -> dict:
    """Get application information including version and feature flags."""
    return {
        "name": settings.name,
        "version": settings.version,
        "environment": settings.env,
        "features": {
            "mcp": settings.enable_mcp,
            "rag": settings.enable_rag,
            "workflows": settings.enable_workflows,
            "analytics": settings.enable_analytics,
        },
    }
