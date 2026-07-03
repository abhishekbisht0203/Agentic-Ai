"""
SQLAlchemy declarative base and common model mixins.

Provides the base class for all database models with common fields.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


class TimestampMixin:
    """Mixin that adds created_at and updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class UUIDMixin:
    """Mixin that adds UUID primary key."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )


class SoftDeleteMixin:
    """Mixin that adds soft delete support."""

    is_deleted: Mapped[bool] = mapped_column(default=False, index=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class BaseModel(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Abstract base model with UUID, timestamps, and soft delete."""

    __abstract__ = True

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.id})>"


class NamedModel(Base, UUIDMixin, TimestampMixin):
    """Abstract model with a name field."""

    __abstract__ = True

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(2048), nullable=True)
