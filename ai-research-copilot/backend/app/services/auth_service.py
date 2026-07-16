"""Authentication service handling login, registration, tokens, and OAuth."""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AuthenticationError, ValidationError
from app.core.security.auth import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    verify_token,
)
from app.models.user import User, UserSession
from app.repositories.user import UserRepository
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
)


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.user_repo = UserRepository(db)

    async def register(self, data: RegisterRequest) -> TokenResponse:
        """Register a new user with email and password.

        Validates uniqueness of email and username, hashes the password,
        creates the user record, and returns tokens.

        Args:
            data: Registration request containing email, username, password.

        Returns:
            TokenResponse with access and refresh tokens.

        Raises:
            ValidationError: If email or username is already taken.
        """
        existing = await self.user_repo.get_by_email(data.email)
        if existing:
            raise ValidationError(message="Email already registered")

        existing_username = await self.user_repo.get_by_username(data.username)
        if existing_username:
            raise ValidationError(message="Username already taken")

        user = await self.user_repo.create_user(
            email=data.email,
            username=data.username,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
        )

        return await self._create_tokens(user)

    async def login(self, data: LoginRequest) -> TokenResponse:
        """Authenticate user with email and password.

        Verifies credentials, checks account status, updates last login
        timestamp, and returns tokens.

        Args:
            data: Login request containing email and password.

        Returns:
            TokenResponse with access and refresh tokens.

        Raises:
            AuthenticationError: If credentials are invalid or account is inactive.
        """
        user = await self.user_repo.get_by_email(data.email)
        if not user or not user.hashed_password:
            raise AuthenticationError(message="Invalid credentials")

        if not verify_password(data.password, user.hashed_password):
            raise AuthenticationError(message="Invalid credentials")

        if not user.is_active:
            raise AuthenticationError(message="Account is deactivated")

        await self.user_repo.update_last_login(user.id)

        return await self._create_tokens(user)

    async def refresh_token(self, data: RefreshTokenRequest) -> TokenResponse:
        """Refresh access token using a valid refresh token.

        Validates the refresh token, verifies the user exists and is active,
        then issues new token pair.

        Args:
            data: Refresh token request containing the refresh token.

        Returns:
            TokenResponse with new access and refresh tokens.

        Raises:
            AuthenticationError: If token is invalid or user is inactive.
        """
        payload = verify_token(data.refresh_token)
        if not payload.refresh:
            raise AuthenticationError(message="Invalid refresh token")

        user = await self.user_repo.get_by_id(uuid.UUID(payload.sub))
        if not user or not user.is_active:
            raise AuthenticationError(message="User not found or inactive")

        return await self._create_tokens(user)

    async def change_password(
        self, user_id: uuid.UUID, data: ChangePasswordRequest
    ) -> None:
        """Change an authenticated user's password.

        Verifies the current password before applying the new one.

        Args:
            user_id: UUID of the user changing their password.
            data: Change password request with current and new passwords.

        Raises:
            AuthenticationError: If user not found or current password is incorrect.
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise AuthenticationError(message="User not found")

        if not user.hashed_password or not verify_password(
            data.current_password, user.hashed_password
        ):
            raise AuthenticationError(message="Current password is incorrect")

        await self.user_repo.update(user_id, hashed_password=hash_password(data.new_password))

    async def logout(self, user_id: uuid.UUID, token: str) -> None:
        """Invalidate a user session by marking it inactive.

        Args:
            user_id: UUID of the user logging out.
            token: The access token to invalidate.
        """
        from sqlalchemy import select

        query = select(UserSession).where(
            UserSession.user_id == user_id,
            UserSession.token == token,
            UserSession.is_active == True,
        )
        result = await self.db.execute(query)
        session = result.scalar_one_or_none()
        if session:
            session.is_active = False
            await self.db.flush()

    async def _create_tokens(self, user: User) -> TokenResponse:
        """Create access and refresh tokens for a user.

        Generates JWT tokens, persists a session record, and returns
        the token response.

        Args:
            user: The authenticated user instance.

        Returns:
            TokenResponse with tokens and expiration metadata.
        """
        access_token = create_access_token(
            subject=str(user.id),
            scopes=[user.role.value] if hasattr(user.role, "value") else [str(user.role)],
        )
        refresh_token = create_refresh_token(subject=str(user.id))

        session = UserSession(
            user_id=user.id,
            token=access_token,
            refresh_token=refresh_token,
            expires_at=datetime.now(timezone.utc)
            + timedelta(hours=settings.jwt.expiration_hours),
        )
        self.db.add(session)
        await self.db.flush()

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.jwt.expiration_hours * 3600,
        )

    async def forgot_password(self, data: PasswordResetRequest) -> dict:
        """Send a password reset email.

        Always returns success to prevent email enumeration.
        In production, this would send an email via SendGrid/Resend/etc.
        """
        user = await self.user_repo.get_by_email(data.email)
        if user:
            reset_token = create_access_token(
                subject=str(user.id),
                scopes=["password_reset"],
                expires_delta=timedelta(hours=1),
            )
            logger.info(
                "Password reset requested for %s (token: %s...)",
                data.email,
                reset_token[:20],
            )
        else:
            logger.info("Password reset requested for unknown email %s", data.email)
        return {"message": "If that email is registered, a reset link has been sent."}

    async def reset_password(self, data: PasswordResetConfirm) -> dict:
        """Reset a user's password using a valid reset token."""
        payload = verify_token(data.token)
        if "password_reset" not in payload.scopes:
            raise AuthenticationError(message="Invalid reset token")
        user = await self.user_repo.get_by_id(uuid.UUID(payload.sub))
        if not user or not user.is_active:
            raise AuthenticationError(message="User not found or inactive")
        await self.user_repo.update(
            user.id,
            hashed_password=hash_password(data.new_password),
        )
        logger.info("Password reset successful for user %s", user.id)
        return {"message": "Password has been reset successfully."}
