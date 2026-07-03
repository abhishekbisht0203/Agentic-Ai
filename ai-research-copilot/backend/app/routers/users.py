"""User management router handling profiles, API keys, and audit logs."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthorizationError
from app.core.security.permissions import Permission, Role, has_permission
from app.database.session import get_db_session
from app.dependencies.auth import get_current_user_from_token, require_role
from app.models.user import User
from app.schemas.user import (
    APIKeyCreate,
    APIKeyResponse,
    AuditLogResponse,
    UserList,
    UserPreferencesUpdate,
    UserResponse,
    UserUpdate,
)
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


def _user_response(user: User) -> dict:
    """Convert a User model to a response dict."""
    return {
        "id": str(user.id),
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "avatar_url": user.avatar_url,
        "role": user.role.value if hasattr(user.role, "value") else str(user.role),
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
    }


@router.get("/", response_model=UserList)
async def list_users(
    current_user: Annotated[User, Depends(require_role(Role.ADMIN))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: str | None = Query(None, description="Search by email, username, or full name"),
) -> UserList:
    """List all users with pagination and optional search.

    Admin only. Supports filtering by email, username, or full name.
    """
    service = UserService(db)
    return await service.list_users(page=page, page_size=page_size, search=search)


@router.get("/me")
async def get_current_user_profile(
    current_user: Annotated[User, Depends(get_current_user_from_token)],
) -> dict:
    """Get the current authenticated user's full profile.

    Returns user details including preferences and account metadata.
    """
    return {
        **_user_response(current_user),
        "oauth_provider": current_user.oauth_provider,
        "last_login_at": current_user.last_login_at.isoformat() if current_user.last_login_at else None,
        "preferences": current_user.preferences,
    }


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: uuid.UUID,
    current_user: Annotated[User, Depends(require_role(Role.ADMIN))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> UserResponse:
    """Get a specific user by their ID.

    Admin only.
    """
    service = UserService(db)
    user = await service.get_user(user_id)
    return UserResponse.model_validate(user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: uuid.UUID,
    data: UserUpdate,
    current_user: Annotated[User, Depends(get_current_user_from_token)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> UserResponse:
    """Update a user's profile information.

    Admin users can update any user. Regular users can only update
    their own profile.
    """
    user_role = Role(current_user.role.value) if hasattr(current_user.role, "value") else Role(current_user.role)
    is_admin = has_permission(user_role, Permission.ALL) or user_role == Role.ADMIN
    is_self = current_user.id == user_id

    if not is_admin and not is_self:
        raise AuthorizationError(message="You can only update your own profile")

    service = UserService(db)
    user = await service.update_user(user_id, data)
    return UserResponse.model_validate(user)


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: uuid.UUID,
    current_user: Annotated[User, Depends(require_role(Role.ADMIN))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> None:
    """Soft-delete a user and all associated data.

    Admin only.
    """
    service = UserService(db)
    await service.delete_user(user_id)


@router.put("/me/preferences")
async def update_own_preferences(
    data: UserPreferencesUpdate,
    current_user: Annotated[User, Depends(get_current_user_from_token)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    """Update the current user's preferences.

    Replaces the entire preferences dictionary with the provided values.
    """
    service = UserService(db)
    updated_prefs = await service.update_preferences(current_user.id, data)
    return {"preferences": updated_prefs}


@router.post("/me/api-keys", response_model=dict, status_code=201)
async def create_api_key(
    data: APIKeyCreate,
    current_user: Annotated[User, Depends(get_current_user_from_token)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    """Create a new API key for the current user.

    Returns the full key value only at creation time. Store it securely
    as it cannot be retrieved later.
    """
    service = UserService(db)
    result = await service.create_api_key(current_user.id, data)
    return {
        "id": str(result.id),
        "name": result.name,
        "key_prefix": result.key_prefix,
        "scopes": result.scopes,
        "is_active": result.is_active,
        "expires_at": result.expires_at.isoformat() if result.expires_at else None,
        "last_used_at": result.last_used_at.isoformat() if result.last_used_at else None,
        "created_at": result.created_at.isoformat() if result.created_at else None,
        "full_key": result.full_key,
    }


@router.get("/me/api-keys", response_model=list[dict])
async def list_api_keys(
    current_user: Annotated[User, Depends(get_current_user_from_token)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[dict]:
    """List all API keys for the current user.

    Does not include full key values for security.
    """
    service = UserService(db)
    keys = await service.list_api_keys(current_user.id)
    return [
        {
            "id": str(k.id),
            "name": k.name,
            "key_prefix": k.key_prefix,
            "scopes": k.scopes,
            "is_active": k.is_active,
            "expires_at": k.expires_at.isoformat() if k.expires_at else None,
            "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
            "created_at": k.created_at.isoformat() if k.created_at else None,
        }
        for k in keys
    ]


@router.delete("/me/api-keys/{key_id}", status_code=204)
async def revoke_api_key(
    key_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user_from_token)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> None:
    """Revoke (deactivate) an API key.

    The key will be marked as inactive and soft-deleted.
    """
    service = UserService(db)
    await service.revoke_api_key(current_user.id, key_id)


@router.get("/me/audit-logs", response_model=list[dict])
async def get_audit_logs(
    current_user: Annotated[User, Depends(get_current_user_from_token)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> list[dict]:
    """Get paginated audit logs for the current user.

    Returns a chronological list of actions performed by the user.
    """
    service = UserService(db)
    logs = await service.get_audit_logs(current_user.id, page=page, page_size=page_size)
    return [
        {
            "id": str(log.id),
            "user_id": str(log.user_id) if log.user_id else None,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": str(log.resource_id) if log.resource_id else None,
            "details": log.details,
            "status": log.status.value if hasattr(log.status, "value") else str(log.status),
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]
