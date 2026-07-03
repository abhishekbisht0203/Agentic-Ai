"""Admin router for administrative operations and system statistics."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.permissions import Role
from app.database.session import get_db_session
from app.dependencies.auth import get_current_user_from_token, require_role
from app.models.user import User
from app.schemas.user import UserList
from app.services.user_service import UserService

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/users", response_model=UserList)
async def list_users(
    current_user: Annotated[User, Depends(require_role(Role.ADMIN))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    search: str | None = Query(default=None, max_length=255),
) -> UserList:
    """List all users with pagination and optional search (admin only)."""
    service = UserService(db)
    return await service.list_users(page, page_size, search)


@router.get("/stats")
async def get_system_stats(
    current_user: Annotated[User, Depends(require_role(Role.ADMIN))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    """Get system-wide statistics (admin only).

    Returns user counts and role distribution.
    """
    total_users = await db.execute(select(func.count()).select_from(User).where(User.is_deleted == False))
    total_count = total_users.scalar() or 0

    active_users = await db.execute(
        select(func.count()).select_from(User).where(User.is_deleted == False, User.is_active == True)
    )
    active_count = active_users.scalar() or 0

    admin_users = await db.execute(
        select(func.count()).select_from(User).where(
            User.is_deleted == False,
            User.role == Role.ADMIN,
        )
    )
    admin_count = admin_users.scalar() or 0

    return {
        "total_users": total_count,
        "active_users": active_count,
        "inactive_users": total_count - active_count,
        "admin_users": admin_count,
    }
