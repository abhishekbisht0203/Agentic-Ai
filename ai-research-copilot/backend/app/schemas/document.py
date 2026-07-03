"""
Document Pydantic v2 schemas.

Request/response schemas for document CRUD, upload, chunking, and listing.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DocumentCreate(BaseModel):
    """Schema for creating a new document."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Human-readable document name. Defaults to the original filename if omitted.",
    )
    knowledge_base_ids: Optional[list[UUID]] = Field(
        default=None,
        description="Knowledge base IDs to associate this document with on creation.",
    )


class DocumentUpdate(BaseModel):
    """Schema for updating an existing document."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Updated human-readable document name.",
    )


class DocumentResponse(BaseModel):
    """Schema for document data returned in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    name: str
    original_filename: str
    mime_type: str
    file_size: int
    status: str
    chunk_count: int
    created_at: datetime
    updated_at: datetime


class DocumentDetail(DocumentResponse):
    """Extended document schema with storage and processing details."""

    storage_backend: str
    content_text: Optional[str] = None
    processing_error: Optional[str] = None
    metadata_extra: Optional[dict] = None


class DocumentList(BaseModel):
    """Paginated list of documents."""

    model_config = ConfigDict(from_attributes=True)

    items: list[DocumentResponse]
    total: int
    page: int
    page_size: int


class DocumentUploadResponse(BaseModel):
    """Response returned after a document upload is accepted."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    status: str
    message: str


class DocumentChunkResponse(BaseModel):
    """Schema for a single document chunk."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    chunk_index: int
    content: str
    token_count: int
    chunk_type: str
    metadata_extra: Optional[dict] = None


class DocumentChunkList(BaseModel):
    """Paginated list of document chunks."""

    model_config = ConfigDict(from_attributes=True)

    items: list[DocumentChunkResponse]
    total: int
