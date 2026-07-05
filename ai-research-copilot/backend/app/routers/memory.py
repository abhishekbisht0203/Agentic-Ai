"""Memory and user-preference API routes."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.dependencies.auth import get_current_user_from_token
from app.models.user import User
from app.schemas.memory import (
    MemoryEntryCreate,
    MemoryEntryList,
    MemoryEntryResponse,
    MemoryEntryUpdate,
    UserPreferenceResponse,
    UserPreferenceUpdate,
)
from app.services.memory_service import MemoryService

router = APIRouter(prefix="/memory", tags=["Memory"])


async def _get_memory_service(
    db: AsyncSession = Depends(get_db_session),
) -> MemoryService:
    """Create a MemoryService instance bound to the request-scoped DB session."""
    return MemoryService(db)


# ------------------------------------------------------------------
# Memory entries
# ------------------------------------------------------------------


@router.post(
    "/entries",
    response_model=MemoryEntryResponse,
    status_code=201,
    summary="Create a memory entry",
)
async def create_memory_entry(
    data: MemoryEntryCreate,
    current_user: User = Depends(get_current_user_from_token),
    memory_service: MemoryService = Depends(_get_memory_service),
) -> MemoryEntryResponse:
    """Create a new long-term memory entry for the authenticated user."""
    return await memory_service.create_memory_entry(user_id=current_user.id, data=data)


@router.get(
    "/entries",
    response_model=MemoryEntryList,
    summary="List memory entries",
)
async def list_memory_entries(
    current_user: User = Depends(get_current_user_from_token),
    memory_service: MemoryService = Depends(_get_memory_service),
    memory_type: Optional[str] = Query(None, description="Filter by memory type"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> MemoryEntryList:
    """Return a paginated list of memory entries, optionally filtered by type."""
    return await memory_service.list_memory_entries(
        user_id=current_user.id,
        memory_type=memory_type,
        page=page,
        page_size=page_size,
    )


@router.put(
    "/entries/{entry_id}",
    response_model=MemoryEntryResponse,
    summary="Update a memory entry",
)
async def update_memory_entry(
    entry_id: uuid.UUID,
    data: MemoryEntryUpdate,
    current_user: User = Depends(get_current_user_from_token),
    memory_service: MemoryService = Depends(_get_memory_service),
) -> MemoryEntryResponse:
    """Update a memory entry (content or active status)."""
    return await memory_service.update_memory_entry(
        entry_id=entry_id, user_id=current_user.id, data=data
    )


@router.delete(
    "/entries/{entry_id}",
    status_code=204,
    summary="Delete a memory entry",
)
async def delete_memory_entry(
    entry_id: uuid.UUID,
    current_user: User = Depends(get_current_user_from_token),
    memory_service: MemoryService = Depends(_get_memory_service),
) -> None:
    """Soft-delete a memory entry."""
    await memory_service.delete_memory_entry(
        entry_id=entry_id, user_id=current_user.id
    )


# ------------------------------------------------------------------
# Search
# ------------------------------------------------------------------


@router.get(
    "/search",
    response_model=list[MemoryEntryResponse],
    summary="Search memory entries",
)
async def search_memory(
    query: str = Query(..., min_length=1, description="Search query"),
    current_user: User = Depends(get_current_user_from_token),
    memory_service: MemoryService = Depends(_get_memory_service),
    limit: int = Query(10, ge=1, le=50, description="Max results"),
) -> list[MemoryEntryResponse]:
    """Search memory entries by content using semantic similarity."""
    return await memory_service.search_memory(
        user_id=current_user.id, query=query, limit=limit
    )


# ------------------------------------------------------------------
# User preferences
# ------------------------------------------------------------------


@router.get(
    "/preferences",
    response_model=list[UserPreferenceResponse],
    summary="Get user preferences",
)
async def get_preferences(
    current_user: User = Depends(get_current_user_from_token),
    memory_service: MemoryService = Depends(_get_memory_service),
) -> list[UserPreferenceResponse]:
    """Return all preferences for the authenticated user."""
    return await memory_service.get_preferences(user_id=current_user.id)


@router.put(
    "/preferences",
    response_model=UserPreferenceResponse,
    summary="Update a user preference",
)
async def update_preference(
    data: UserPreferenceUpdate,
    current_user: User = Depends(get_current_user_from_token),
    memory_service: MemoryService = Depends(_get_memory_service),
) -> UserPreferenceResponse:
    """Create or update a user preference (upsert by category + key)."""
    return await memory_service.update_preference(user_id=current_user.id, data=data)
