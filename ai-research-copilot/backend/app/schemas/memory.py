"""
Memory and user-preference Pydantic v2 schemas.

Request/response schemas for long-term memory entries,
semantic search, and user preference management.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MemoryEntryCreate(BaseModel):
    """Schema for creating a new memory entry."""

    model_config = ConfigDict(str_strip_whitespace=True)

    content: str = Field(
        ...,
        min_length=1,
        description="The memory content to store.",
    )
    memory_type: str = Field(
        ...,
        max_length=30,
        description="Category of memory (e.g. 'semantic', 'factual', 'episodic', 'preference').",
    )
    source: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Origin of the memory (e.g. conversation ID, document reference).",
    )
    metadata_extra: Optional[dict] = Field(
        default=None,
        description="Arbitrary JSON metadata attached to the memory entry.",
    )

    @field_validator("memory_type")
    @classmethod
    def validate_memory_type(cls, v: str) -> str:
        """Validate the memory type is a recognised value."""
        allowed = {"semantic", "factual", "episodic", "preference"}
        if v not in allowed:
            raise ValueError(f"Memory type must be one of {sorted(allowed)}")
        return v


class MemoryEntryUpdate(BaseModel):
    """Schema for updating an existing memory entry."""

    model_config = ConfigDict(str_strip_whitespace=True)

    content: Optional[str] = Field(
        default=None,
        min_length=1,
        description="Updated memory content.",
    )
    is_active: Optional[bool] = Field(
        default=None,
        description="Set to false to soft-deactivate the memory entry.",
    )


class MemoryEntryResponse(BaseModel):
    """Schema for a memory entry returned in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    memory_type: str
    content: str
    source: Optional[str] = None
    relevance_score: Optional[float] = None
    is_active: bool
    created_at: datetime


class MemoryEntryList(BaseModel):
    """Paginated list of memory entries."""

    model_config = ConfigDict(from_attributes=True)

    items: list[MemoryEntryResponse]
    total: int


class UserPreferenceUpdate(BaseModel):
    """Schema for creating or updating a user preference."""

    model_config = ConfigDict(str_strip_whitespace=True)

    category: str = Field(
        ...,
        max_length=50,
        description="Preference category (e.g. 'llm', 'ui', 'notifications').",
    )
    key: str = Field(
        ...,
        max_length=100,
        description="Preference key within the category.",
    )
    value: dict = Field(
        ...,
        description="Preference value stored as an arbitrary JSON object.",
    )


class UserPreferenceResponse(BaseModel):
    """Schema for a user preference returned in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    category: str
    key: str
    value: dict
    created_at: datetime


class UserPreferenceList(BaseModel):
    """List of user preferences (no pagination required for preferences)."""

    model_config = ConfigDict(from_attributes=True)

    items: list[UserPreferenceResponse]
