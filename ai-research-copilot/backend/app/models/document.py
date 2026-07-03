"""
Document and knowledge base models.

Provides SQLAlchemy models for document storage, chunking, and RAG operations.
"""

import uuid
from typing import List, Optional

from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, BaseModel


class Document(BaseModel):
    """
    Uploaded documents with metadata and processing status.

    Stores information about uploaded files, their content, and processing state.
    Supports S3 and local storage backends.
    """

    __tablename__ = "documents"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    original_filename: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
    )
    mime_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    file_size: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )
    storage_path: Mapped[str] = mapped_column(
        String(1024),
        nullable=False,
    )
    storage_backend: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="local",
    )
    content_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="processing",
        index=True,
    )
    metadata_extra: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )
    processing_error: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    chunk_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # Relationships
    chunks: Mapped[List["DocumentChunk"]] = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    knowledge_bases: Mapped[List["KnowledgeBase"]] = relationship(
        "KnowledgeBase",
        secondary="knowledge_base_documents",
        back_populates="documents",
        lazy="selectin",
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="documents",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, name='{self.name}', status='{self.status}')>"


class DocumentChunk(BaseModel):
    """
    Document chunks for RAG operations.

    Stores chunked content with embeddings for semantic search.
    Supports parent-child chunking strategies.
    """

    __tablename__ = "document_chunks"

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    token_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    embedding_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )
    metadata_extra: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )
    parent_chunk_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document_chunks.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    chunk_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="semantic",
    )

    # Relationships
    document: Mapped["Document"] = relationship(
        "Document",
        back_populates="chunks",
        lazy="selectin",
    )
    parent_chunk: Mapped[Optional["DocumentChunk"]] = relationship(
        "DocumentChunk",
        remote_side="DocumentChunk.id",
        back_populates="child_chunks",
        lazy="selectin",
    )
    child_chunks: Mapped[List["DocumentChunk"]] = relationship(
        "DocumentChunk",
        back_populates="parent_chunk",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<DocumentChunk(id={self.id}, document_id={self.document_id}, "
            f"index={self.chunk_index}, type='{self.chunk_type}')>"
        )


class KnowledgeBase(BaseModel):
    """
    Collections of documents for RAG.

    Groups documents together with shared embedding models and settings.
    """

    __tablename__ = "knowledge_bases"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(2048),
        nullable=True,
    )
    embedding_model: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="text-embedding-ada-002",
    )
    document_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    chunk_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    is_public: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    settings_extra: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Relationships
    documents: Mapped[List["Document"]] = relationship(
        "Document",
        secondary="knowledge_base_documents",
        back_populates="knowledge_bases",
        lazy="selectin",
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="knowledge_bases",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<KnowledgeBase(id={self.id}, name='{self.name}', "
            f"documents={self.document_count})>"
        )


class KnowledgeBaseDocument(Base):
    """
    Junction table linking knowledge bases to documents.

    Many-to-many relationship between knowledge bases and documents.
    """

    __tablename__ = "knowledge_base_documents"

    knowledge_base_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_bases.id", ondelete="CASCADE"),
        primary_key=True,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        primary_key=True,
    )

    def __repr__(self) -> str:
        return (
            f"<KnowledgeBaseDocument(kb_id={self.knowledge_base_id}, "
            f"doc_id={self.document_id})>"
        )
