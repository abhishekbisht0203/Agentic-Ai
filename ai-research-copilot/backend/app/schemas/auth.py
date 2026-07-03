"""
Authentication schemas for request/response validation.

Provides Pydantic v2 models for login, registration, token management,
password reset, and OAuth callback operations.
"""

import re
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class OAuthProvider(str, Enum):
    """Supported OAuth providers."""

    GITHUB = "github"
    GOOGLE = "google"
    MICROSOFT = "microsoft"


class TokenResponse(BaseModel):
    """Response schema returned after successful authentication.

    Contains the access and refresh tokens along with metadata
    required by clients to manage authenticated sessions.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    access_token: str = Field(
        ..., description="JWT access token for API authentication"
    )
    refresh_token: str = Field(
        ..., description="Refresh token for obtaining new access tokens"
    )
    token_type: str = Field(
        default="bearer",
        description="Token type, always 'bearer' for JWT tokens",
    )
    expires_in: int = Field(
        ...,
        gt=0,
        description="Access token lifetime in seconds",
    )


class TokenPayload(BaseModel):
    """JWT token payload structure.

    Mirrors the standard JWT claims used throughout the application
    for token creation and verification.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    sub: str = Field(
        ..., description="Subject claim, typically the user ID"
    )
    exp: datetime | None = Field(
        default=None, description="Token expiration timestamp"
    )
    iat: datetime | None = Field(
        default=None, description="Token issued-at timestamp"
    )
    refresh: bool = Field(
        default=False,
        description="Whether this is a refresh token",
    )
    scopes: list[str] = Field(
        default_factory=list,
        description="List of permission scopes granted by this token",
    )


class LoginRequest(BaseModel):
    """Request schema for email/password authentication."""

    model_config = ConfigDict(str_strip_whitespace=True)

    email: str = Field(
        ...,
        min_length=5,
        max_length=255,
        description="User email address",
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="User password",
    )

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, v):
            raise ValueError("Invalid email address format")
        return v.lower()


class RegisterRequest(BaseModel):
    """Request schema for new user registration."""

    model_config = ConfigDict(str_strip_whitespace=True)

    email: str = Field(
        ...,
        min_length=5,
        max_length=255,
        description="User email address",
    )
    username: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Unique username for the account",
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password for the new account",
    )
    full_name: str | None = Field(
        default=None,
        max_length=255,
        description="Optional full name of the user",
    )

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, v):
            raise ValueError("Invalid email address format")
        return v.lower()

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username contains only allowed characters."""
        pattern = r"^[a-zA-Z0-9_-]+$"
        if not re.match(pattern, v):
            raise ValueError(
                "Username must contain only letters, numbers, underscores, and hyphens"
            )
        return v.lower()


class RefreshTokenRequest(BaseModel):
    """Request schema for refreshing an access token."""

    model_config = ConfigDict(str_strip_whitespace=True)

    refresh_token: str = Field(
        ...,
        min_length=1,
        description="Valid refresh token",
    )


class PasswordResetRequest(BaseModel):
    """Request schema for initiating a password reset."""

    model_config = ConfigDict(str_strip_whitespace=True)

    email: str = Field(
        ...,
        min_length=5,
        max_length=255,
        description="Email address associated with the account",
    )

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, v):
            raise ValueError("Invalid email address format")
        return v.lower()


class PasswordResetConfirm(BaseModel):
    """Request schema for confirming a password reset with a token."""

    model_config = ConfigDict(str_strip_whitespace=True)

    token: str = Field(
        ...,
        min_length=1,
        description="Password reset token received via email",
    )
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password to set for the account",
    )


class ChangePasswordRequest(BaseModel):
    """Request schema for changing an authenticated user's password."""

    model_config = ConfigDict(str_strip_whitespace=True)

    current_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Current password for verification",
    )
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password to replace the current one",
    )

    @field_validator("new_password")
    @classmethod
    def validate_new_password_strength(cls, v: str) -> str:
        """Validate new password meets minimum strength requirements."""
        if not re.search(r"[A-Z]", v):
            raise ValueError("New password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("New password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("New password must contain at least one digit")
        return v


class OAuthCallbackRequest(BaseModel):
    """Request schema for handling OAuth provider callback."""

    model_config = ConfigDict(str_strip_whitespace=True)

    provider: OAuthProvider = Field(
        ...,
        description="OAuth provider name (github, google, or microsoft)",
    )
    code: str = Field(
        ...,
        min_length=1,
        description="Authorization code from the OAuth provider",
    )
    state: str = Field(
        ...,
        min_length=1,
        description="State parameter for CSRF protection",
    )
