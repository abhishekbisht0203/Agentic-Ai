"""
User-related SQLAlchemy models.

Defines User, UserSession, APIKey, and AuditLog models for authentication,
authorization, and audit trail functionality.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseModel


class UserRole(str, enum.Enum):
    """Enumeration of user roles."""

    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"
    GUEST = "guest"


class AuditLogStatus(str, enum.Enum):
    """Enumeration of audit log statuses."""

    SUCCESS = "success"
    FAILURE = "failure"


class User(BaseModel):
    """User model representing system users.

    Supports both local authentication (email/password) and OAuth providers
    (GitHub, Google, Microsoft). Stores user preferences as JSONB.
    """

    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_email", "email"),
        Index("ix_users_username", "username"),
        {"comment": "System users"},
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        comment="User email address",
    )
    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        comment="Unique username",
    )
    hashed_password: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Hashed password (null for OAuth users)",
    )
    full_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="User's full name",
    )
    avatar_url: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
        comment="URL to user avatar image",
    )
    role: Mapped[UserRole] = mapped_column(
        String(20),
        default=UserRole.USER,
        nullable=False,
        comment="User role for access control",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether the user account is active",
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether the user email is verified",
    )
    oauth_provider: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="OAuth provider (github, google, microsoft)",
    )
    oauth_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="OAuth provider user ID",
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of last successful login",
    )
    preferences: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="User preferences stored as JSON",
    )

    sessions: Mapped[list["UserSession"]] = relationship(
        "UserSession",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    api_keys: Mapped[list["APIKey"]] = relationship(
        "APIKey",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="noload",
    )
    documents: Mapped[list["Document"]] = relationship(
        "Document",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="noload",
    )
    knowledge_bases: Mapped[list["KnowledgeBase"]] = relationship(
        "KnowledgeBase",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="noload",
    )
    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="noload",
    )
    bookmarks: Mapped[list["ConversationBookmark"]] = relationship(
        "ConversationBookmark",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="noload",
    )
    memory_entries: Mapped[list["MemoryEntry"]] = relationship(
        "MemoryEntry",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="noload",
    )
    user_preferences: Mapped[list["UserPreference"]] = relationship(
        "UserPreference",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="noload",
    )
    analytics_reports: Mapped[list["AnalyticsReport"]] = relationship(
        "AnalyticsReport",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="noload",
    )
    visualizations: Mapped[list["Visualization"]] = relationship(
        "Visualization",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="noload",
    )
    activities: Mapped[list["UserActivity"]] = relationship(
        "UserActivity",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="noload",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, username={self.username})>"


class UserSession(BaseModel):
    """Active user session tracking.

    Stores session tokens for authenticated users with IP and user agent
    information for security auditing.
    """

    __tablename__ = "user_sessions"
    __table_args__ = (
        Index("ix_user_sessions_user_id", "user_id"),
        Index("ix_user_sessions_token", "token"),
        {"comment": "Active user sessions"},
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to the user",
    )
    token: Mapped[str] = mapped_column(
        String(512),
        unique=True,
        nullable=False,
        comment="Session token",
    )
    refresh_token: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
        comment="Refresh token for session renewal",
    )
    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
        comment="Client IP address",
    )
    user_agent: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
        comment="Client user agent string",
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Session expiration timestamp",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether the session is active",
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="sessions",
    )

    def __repr__(self) -> str:
        return f"<UserSession(id={self.id}, user_id={self.user_id})>"


class APIKey(BaseModel):
    """API key for programmatic access.

    Stores hashed API keys with scoped permissions and usage tracking.
    The key_prefix field stores the first 8 characters for identification
    without exposing the full key.
    """

    __tablename__ = "api_keys"
    __table_args__ = (
        Index("ix_api_keys_user_id", "user_id"),
        Index("ix_api_keys_key_hash", "key_hash"),
        {"comment": "API keys for programmatic access"},
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to the owner user",
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Human-readable API key name",
    )
    key_hash: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        comment="Hashed API key value",
    )
    key_prefix: Mapped[str] = mapped_column(
        String(8),
        nullable=False,
        comment="First 8 characters of the key for identification",
    )
    scopes: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        comment="List of permission scope strings",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether the API key is active",
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="API key expiration timestamp",
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of last API key usage",
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="api_keys",
    )

    def __repr__(self) -> str:
        return f"<APIKey(id={self.id}, name={self.name}, prefix={self.key_prefix})>"


class AuditLog(BaseModel):
    """System audit trail for tracking user actions.

    Records all significant actions performed in the system for
    compliance and debugging purposes.
    """

    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_user_id", "user_id"),
        Index("ix_audit_logs_action", "action"),
        Index("ix_audit_logs_resource_type", "resource_type"),
        Index("ix_audit_logs_created_at", "created_at"),
        {"comment": "System audit trail"},
    )

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="Reference to the user (null for system actions)",
    )
    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Action performed (e.g., create, update, delete)",
    )
    resource_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Type of resource affected (e.g., user, document)",
    )
    resource_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="ID of the affected resource",
    )
    details: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Additional details about the action",
    )
    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
        comment="Client IP address",
    )
    user_agent: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
        comment="Client user agent string",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Action status (success or failure)",
    )

    user: Mapped["User | None"] = relationship(
        "User",
        back_populates="audit_logs",
    )

    def __repr__(self) -> str:
        return (
            f"<AuditLog(id={self.id}, action={self.action}, "
            f"resource_type={self.resource_type})>"
        )
