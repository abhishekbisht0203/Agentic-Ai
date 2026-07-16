"""Authentication router handling login, registration, token management, and user info."""

import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database.session import get_db_session
from app.dependencies.auth import get_current_user_from_token
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
)
from app.services.auth_service import AuthService
from app.services.oauth_service import OAuthService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

security = HTTPBearer(auto_error=False)


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    """Register a new user with email, username, and password."""
    service = AuthService(db)
    return await service.register(data)


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    """Authenticate a user with email and password."""
    service = AuthService(db)
    return await service.login(data)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    """Refresh an access token using a valid refresh token."""
    service = AuthService(db)
    return await service.refresh_token(data)


@router.post("/change-password", status_code=204)
async def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """Change the authenticated user's password."""
    service = AuthService(db)
    await service.change_password(current_user.id, data)


@router.post("/logout", status_code=204)
async def logout(
    current_user: User = Depends(get_current_user_from_token),
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """Log out the current user by invalidating their session."""
    service = AuthService(db)
    token = credentials.credentials if credentials else ""
    await service.logout(current_user.id, token)


@router.get("/me")
async def get_current_user(
    current_user: User = Depends(get_current_user_from_token),
) -> dict:
    """Get the current authenticated user's profile information."""
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


# ==================== Password Reset Endpoints ====================


@router.post("/forgot-password", status_code=200)
async def forgot_password(
    data: PasswordResetRequest,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Request a password reset email."""
    service = AuthService(db)
    return await service.forgot_password(data)


@router.post("/reset-password", status_code=200)
async def reset_password(
    data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Reset a password using a reset token."""
    service = AuthService(db)
    return await service.reset_password(data)


# ==================== OAuth Endpoints ====================


@router.get("/google/login")
async def google_login() -> RedirectResponse:
    """Initiate Google OAuth login flow."""
    if not settings.oauth.google_client_id:
        return RedirectResponse(
            url=f"{settings.oauth.frontend_url}/login?error=oauth_disabled"
        )

    state = OAuthService.generate_state("google")
    auth_url = OAuthService.get_google_auth_url(state)
    return RedirectResponse(url=auth_url)


@router.get("/google/callback")
async def google_callback(
    code: str = Query(..., description="Authorization code from Google"),
    state: str = Query(..., description="State parameter for CSRF protection"),
    db: AsyncSession = Depends(get_db_session),
) -> RedirectResponse:
    """Handle Google OAuth callback."""
    try:
        await OAuthService.verify_state(state)
        oauth_service = OAuthService(db)
        user_info = await oauth_service.exchange_google_code(code)
        token_response = await oauth_service.authenticate_oauth_user(user_info, "google")

        redirect_url = (
            f"{settings.oauth.frontend_url}/auth/callback"
            f"#access_token={token_response.access_token}"
            f"&refresh_token={token_response.refresh_token}"
            f"&token_type={token_response.token_type}"
            f"&expires_in={token_response.expires_in}"
        )
        return RedirectResponse(url=redirect_url)

    except Exception as e:
        logger.exception("Google OAuth callback failed")
        return RedirectResponse(
            url=f"{settings.oauth.frontend_url}/login?error=oauth_failed"
        )


@router.get("/github/login")
async def github_login() -> RedirectResponse:
    """Initiate GitHub OAuth login flow."""
    if not settings.oauth.github_client_id:
        return RedirectResponse(
            url=f"{settings.oauth.frontend_url}/login?error=oauth_disabled"
        )

    state = OAuthService.generate_state("github")
    auth_url = OAuthService.get_github_auth_url(state)
    return RedirectResponse(url=auth_url)


@router.get("/github/callback")
async def github_callback(
    code: str = Query(..., description="Authorization code from GitHub"),
    state: str = Query(..., description="State parameter for CSRF protection"),
    db: AsyncSession = Depends(get_db_session),
) -> RedirectResponse:
    """Handle GitHub OAuth callback."""
    try:
        await OAuthService.verify_state(state)
        oauth_service = OAuthService(db)
        user_info = await oauth_service.exchange_github_code(code)
        token_response = await oauth_service.authenticate_oauth_user(user_info, "github")

        redirect_url = (
            f"{settings.oauth.frontend_url}/auth/callback"
            f"#access_token={token_response.access_token}"
            f"&refresh_token={token_response.refresh_token}"
            f"&token_type={token_response.token_type}"
            f"&expires_in={token_response.expires_in}"
        )
        return RedirectResponse(url=redirect_url)

    except Exception as e:
        logger.exception("GitHub OAuth callback failed")
        return RedirectResponse(
            url=f"{settings.oauth.frontend_url}/login?error=oauth_failed"
        )
