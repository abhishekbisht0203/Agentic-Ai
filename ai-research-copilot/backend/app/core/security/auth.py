"""
Authentication utilities for JWT token management and password handling.

Provides secure token creation, verification, and password hashing.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import jwt, JWTError
from pydantic import BaseModel

from app.core.config import settings
from app.core.exceptions import AuthenticationError


class TokenPayload(BaseModel):
    """JWT token payload structure."""

    sub: str  # Subject (user ID)
    exp: datetime | None = None
    iat: datetime | None = None
    refresh: bool = False
    scopes: list[str] = []


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password to hash.

    Returns:
        Hashed password string.
    """
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password to verify.
        hashed_password: Hashed password to check against.

    Returns:
        True if password matches, False otherwise.
    """
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(
    subject: str | Any,
    expires_delta: timedelta | None = None,
    scopes: list[str] | None = None,
) -> str:
    """
    Create a JWT access token.

    Args:
        subject: Token subject (typically user ID).
        expires_delta: Optional custom expiration time.
        scopes: Optional list of permission scopes.

    Returns:
        Encoded JWT token string.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=settings.jwt.expiration_hours)

    payload = TokenPayload(
        sub=str(subject),
        exp=expire,
        iat=datetime.now(timezone.utc),
        refresh=False,
        scopes=scopes or [],
    )

    encoded_jwt = jwt.encode(
        payload.model_dump(),
        settings.jwt.secret_key,
        algorithm=settings.jwt.algorithm,
    )
    return encoded_jwt


def create_refresh_token(
    subject: str | Any,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a JWT refresh token.

    Args:
        subject: Token subject (typically user ID).
        expires_delta: Optional custom expiration time.

    Returns:
        Encoded JWT refresh token string.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.jwt.refresh_expiration_days)

    payload = TokenPayload(
        sub=str(subject),
        exp=expire,
        iat=datetime.now(timezone.utc),
        refresh=True,
    )

    encoded_jwt = jwt.encode(
        payload.model_dump(),
        settings.jwt.secret_key,
        algorithm=settings.jwt.algorithm,
    )
    return encoded_jwt


def verify_token(token: str) -> TokenPayload:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token string to verify.

    Returns:
        Decoded TokenPayload if valid.

    Raises:
        AuthenticationError: If token is invalid or expired.
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt.secret_key,
            algorithms=[settings.jwt.algorithm],
        )
        return TokenPayload(**payload)
    except JWTError as e:
        raise AuthenticationError(
            message="Invalid or expired token",
            details={"error": str(e)},
        )


async def get_current_user(token: str) -> dict[str, Any]:
    """
    Get current user from JWT token.

    Args:
        token: JWT token string.

    Returns:
        User information dictionary.

    Raises:
        AuthenticationError: If token is invalid.
    """
    payload = verify_token(token)
    return {"user_id": payload.sub, "scopes": payload.scopes}