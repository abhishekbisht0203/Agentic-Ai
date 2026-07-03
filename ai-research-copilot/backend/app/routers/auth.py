"""Authentication router handling login, registration, token management, and user info."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.dependencies.auth import get_current_user_from_token
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])

security = HTTPBearer(auto_error=False)


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    data: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TokenResponse:
    """Register a new user with email, username, and password.

    No authentication required. Returns access and refresh tokens
    upon successful registration.
    """
    service = AuthService(db)
    return await service.register(data)


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TokenResponse:
    """Authenticate a user with email and password.

    No authentication required. Returns access and refresh tokens
    upon successful authentication.
    """
    service = AuthService(db)
    return await service.login(data)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    data: RefreshTokenRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TokenResponse:
    """Refresh an access token using a valid refresh token.

    No authentication required. Returns a new token pair.
    """
    service = AuthService(db)
    return await service.refresh_token(data)


@router.post("/change-password", status_code=204)
async def change_password(
    data: ChangePasswordRequest,
    current_user: Annotated[User, Depends(get_current_user_from_token)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> None:
    """Change the authenticated user's password.

    Requires authentication. Verifies the current password before
    applying the new one.
    """
    service = AuthService(db)
    await service.change_password(current_user.id, data)


@router.post("/logout", status_code=204)
async def logout(
    current_user: Annotated[User, Depends(get_current_user_from_token)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> None:
    """Log out the current user by invalidating their session.

    Requires authentication. Marks the current session as inactive.
    """
    service = AuthService(db)
    token = credentials.credentials if credentials else ""
    await service.logout(current_user.id, token)


@router.get("/me")
async def get_current_user(
    current_user: Annotated[User, Depends(get_current_user_from_token)],
) -> dict:
    """Get the current authenticated user's profile information.

    Requires authentication. Returns user details including
    email, username, role, and account status.
    """
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "avatar_url": current_user.avatar_url,
        "role": current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role),
        "is_active": current_user.is_active,
        "is_verified": current_user.is_verified,
        "oauth_provider": current_user.oauth_provider,
        "last_login_at": current_user.last_login_at.isoformat() if current_user.last_login_at else None,
        "preferences": current_user.preferences,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        "updated_at": current_user.updated_at.isoformat() if current_user.updated_at else None,
    }
