"""
User-related schemas for request/response validation.

Provides Pydantic v2 models for user management, sessions, API keys,
audit logs, and user preferences.
"""

import re
import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserRole(str, Enum):
    """User roles for access control."""

    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"
    GUEST = "guest"


class AuditLogStatus(str, Enum):
    """Audit log action status."""

    SUCCESS = "success"
    FAILURE = "failure"


class UserBase(BaseModel):
    """Base schema containing common user fields.

    Used as the foundation for user creation, update, and response schemas.
    """

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
        description="Unique username",
    )
    full_name: str | None = Field(
        default=None,
        max_length=255,
        description="User's full name",
    )
    avatar_url: str | None = Field(
        default=None,
        max_length=512,
        description="URL to user avatar image",
    )
    role: UserRole = Field(
        default=UserRole.USER,
        description="User role for access control",
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


class UserCreate(UserBase):
    """Schema for creating a new user account.

    Extends UserBase with a password field required for local authentication.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="User password",
    )

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password meets minimum strength requirements."""
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserUpdate(BaseModel):
    """Schema for updating user profile fields.

    All fields are optional; only provided fields will be updated.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    email: str | None = Field(
        default=None,
        min_length=5,
        max_length=255,
        description="Updated email address",
    )
    username: str | None = Field(
        default=None,
        min_length=3,
        max_length=100,
        description="Updated username",
    )
    full_name: str | None = Field(
        default=None,
        max_length=255,
        description="Updated full name",
    )
    avatar_url: str | None = Field(
        default=None,
        max_length=512,
        description="Updated avatar URL",
    )

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str | None) -> str | None:
        """Validate email format when provided."""
        if v is None:
            return v
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, v):
            raise ValueError("Invalid email address format")
        return v.lower()

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str | None) -> str | None:
        """Validate username when provided."""
        if v is None:
            return v
        pattern = r"^[a-zA-Z0-9_-]+$"
        if not re.match(pattern, v):
            raise ValueError(
                "Username must contain only letters, numbers, underscores, and hyphens"
            )
        return v.lower()


class UserResponse(UserBase):
    """Schema for user data returned in API responses.

    Includes read-only fields that are managed by the system.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(
        ..., description="Unique user identifier"
    )
    is_active: bool = Field(
        default=True,
        description="Whether the user account is active",
    )
    is_verified: bool = Field(
        default=False,
        description="Whether the user email is verified",
    )
    created_at: datetime = Field(
        ..., description="Account creation timestamp"
    )
    updated_at: datetime = Field(
        ..., description="Last account update timestamp"
    )


class UserDetail(UserResponse):
    """Detailed user schema including authentication metadata.

    Extends UserResponse with OAuth and session information.
    """

    model_config = ConfigDict(from_attributes=True)

    oauth_provider: str | None = Field(
        default=None,
        max_length=50,
        description="OAuth provider if authenticated via OAuth",
    )
    last_login_at: datetime | None = Field(
        default=None,
        description="Timestamp of last successful login",
    )
    preferences: dict | None = Field(
        default=None,
        description="User preferences stored as JSON",
    )


class UserList(BaseModel):
    """Paginated list of users returned by list endpoints."""

    model_config = ConfigDict(str_strip_whitespace=True)

    items: list[UserResponse] = Field(
        default_factory=list,
        description="List of user records for the current page",
    )
    total: int = Field(
        ...,
        ge=0,
        description="Total number of users matching the query",
    )
    page: int = Field(
        ...,
        ge=1,
        description="Current page number (1-indexed)",
    )
    page_size: int = Field(
        ...,
        ge=1,
        le=100,
        description="Number of items per page",
    )


class UserSessionResponse(BaseModel):
    """Schema for user session data returned in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(
        ..., description="Unique session identifier"
    )
    token: str = Field(
        ...,
        description="Session token value",
    )
    ip_address: str | None = Field(
        default=None,
        max_length=45,
        description="Client IP address",
    )
    user_agent: str | None = Field(
        default=None,
        max_length=512,
        description="Client user agent string",
    )
    expires_at: datetime = Field(
        ..., description="Session expiration timestamp"
    )
    is_active: bool = Field(
        default=True,
        description="Whether the session is currently active",
    )
    created_at: datetime = Field(
        ..., description="Session creation timestamp"
    )


class APIKeyCreate(BaseModel):
    """Schema for creating a new API key."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Human-readable name for the API key",
    )
    scopes: list[str] | None = Field(
        default=None,
        description="Permission scopes for the API key (empty list if omitted)",
    )
    expires_at: datetime | None = Field(
        default=None,
        description="Expiration timestamp (null for non-expiring keys)",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate API key name is not empty after stripping."""
        if not v.strip():
            raise ValueError("API key name cannot be empty")
        return v.strip()


class APIKeyResponse(BaseModel):
    """Schema for API key data returned in API responses.

    Does NOT include the full key value for security reasons.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(
        ..., description="Unique API key identifier"
    )
    name: str = Field(
        ..., description="Human-readable name for the API key"
    )
    key_prefix: str = Field(
        ...,
        min_length=8,
        max_length=8,
        description="First 8 characters of the key for identification",
    )
    scopes: list[str] = Field(
        default_factory=list,
        description="Permission scopes assigned to the key",
    )
    is_active: bool = Field(
        default=True,
        description="Whether the API key is active",
    )
    expires_at: datetime | None = Field(
        default=None,
        description="API key expiration timestamp",
    )
    last_used_at: datetime | None = Field(
        default=None,
        description="Timestamp of last API key usage",
    )
    created_at: datetime = Field(
        ..., description="API key creation timestamp"
    )


class APIKeyCreated(APIKeyResponse):
    """Schema returned only on API key creation.

    Extends APIKeyResponse with the full key value, which is only
    available at creation time and cannot be retrieved later.
    """

    model_config = ConfigDict(from_attributes=True)

    full_key: str = Field(
        ...,
        min_length=1,
        description="Full API key value (only shown once at creation)",
    )


class AuditLogResponse(BaseModel):
    """Schema for audit log entries returned in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(
        ..., description="Unique audit log entry identifier"
    )
    user_id: uuid.UUID | None = Field(
        default=None,
        description="ID of the user who performed the action (null for system actions)",
    )
    action: str = Field(
        ...,
        max_length=100,
        description="Action performed (e.g., create, update, delete)",
    )
    resource_type: str = Field(
        ...,
        max_length=100,
        description="Type of resource affected (e.g., user, document)",
    )
    resource_id: uuid.UUID | None = Field(
        default=None,
        description="ID of the affected resource",
    )
    details: dict | None = Field(
        default=None,
        description="Additional details about the action",
    )
    status: AuditLogStatus = Field(
        ...,
        description="Action status (success or failure)",
    )
    created_at: datetime = Field(
        ..., description="Timestamp when the action was logged"
    )


class UserPreferencesUpdate(BaseModel):
    """Schema for updating user preferences.

    Accepts a dictionary of preference key-value pairs. Existing
    preferences are replaced with the provided values.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    preferences: dict = Field(
        ...,
        description="Dictionary of user preferences to set",
    )

    @field_validator("preferences")
    @classmethod
    def validate_preferences(cls, v: dict) -> dict:
        """Validate preferences dictionary is not empty and has valid structure."""
        if not v:
            raise ValueError("Preferences cannot be empty")
        for key, value in v.items():
            if not isinstance(key, str) or not key.strip():
                raise ValueError("Preference keys must be non-empty strings")
        return v
