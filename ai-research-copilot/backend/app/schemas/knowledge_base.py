"""
Knowledge base Pydantic v2 schemas.

Request/response schemas for knowledge base CRUD, document management, and listing.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class KnowledgeBaseCreate(BaseModel):
    """Schema for creating a new knowledge base."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Human-readable knowledge base name.",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=2048,
        description="Optional description of the knowledge base purpose and contents.",
    )
    embedding_model: Optional[str] = Field(
        default="text-embedding-ada-002",
        max_length=100,
        description="Embedding model identifier used for vectorising chunks.",
    )
    is_public: Optional[bool] = Field(
        default=False,
        description="Whether the knowledge base is publicly accessible.",
    )


class KnowledgeBaseUpdate(BaseModel):
    """Schema for updating an existing knowledge base."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Updated knowledge base name.",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=2048,
        description="Updated description.",
    )
    is_public: Optional[bool] = Field(
        default=None,
        description="Updated public visibility flag.",
    )


class KnowledgeBaseResponse(BaseModel):
    """Schema for knowledge base data returned in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    name: str
    description: Optional[str] = None
    embedding_model: str
    document_count: int
    chunk_count: int
    is_public: bool
    created_at: datetime
    updated_at: datetime


class KnowledgeBaseDetail(KnowledgeBaseResponse):
    """Extended knowledge base schema with full settings."""

    settings_extra: Optional[dict] = None


class KnowledgeBaseList(BaseModel):
    """Paginated list of knowledge bases."""

    model_config = ConfigDict(from_attributes=True)

    items: list[KnowledgeBaseResponse]
    total: int
    page: int
    page_size: int


class KnowledgeBaseAddDocuments(BaseModel):
    """Schema for adding documents to a knowledge base."""

    document_ids: list[UUID] = Field(
        ...,
        min_length=1,
        description="List of document IDs to add to the knowledge base.",
    )


class KnowledgeBaseRemoveDocuments(BaseModel):
    """Schema for removing documents from a knowledge base."""

    document_ids: list[UUID] = Field(
        ...,
        min_length=1,
        description="List of document IDs to remove from the knowledge base.",
    )
