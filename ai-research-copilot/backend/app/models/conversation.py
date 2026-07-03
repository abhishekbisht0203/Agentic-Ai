"""
SQLAlchemy models for conversations, messages, and related entities.

Provides models for chat conversations, individual messages, bookmarks,
long-term memory entries, and user preferences.
"""

import uuid
from typing import Optional

from sqlalchemy import (
    Boolean,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, BaseModel


class Conversation(BaseModel):
    """
    Chat conversations between users and agents.

    Tracks conversation metadata including the agent type, model used,
    status, and token usage statistics.
    """

    __tablename__ = "conversations"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    agent_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    model_used: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="active",
        index=True,
    )
    message_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    token_usage: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    metadata_extra: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    knowledge_base_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_bases.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Relationships
    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )
    bookmarks: Mapped[list["ConversationBookmark"]] = relationship(
        "ConversationBookmark",
        back_populates="conversation",
        cascade="all, delete-orphan",
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="conversations",
        lazy="select",
    )

    def __repr__(self) -> str:
        return (
            f"<Conversation(id={self.id}, title='{self.title}', "
            f"status='{self.status}')>"
        )


class Message(BaseModel):
    """
    Individual messages within a conversation.

    Supports threaded messages via parent_message_id and includes
    tool call tracking and citation references.
    """

    __tablename__ = "messages"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    model_used: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    token_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    metadata_extra: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    parent_message_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("messages.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    agent_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    tool_calls: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    citations: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)

    # Relationships
    conversation: Mapped["Conversation"] = relationship(
        "Conversation",
        back_populates="messages",
    )
    parent_message: Mapped[Optional["Message"]] = relationship(
        "Message",
        remote_side="Message.id",
        back_populates="replies",
        lazy="select",
    )
    replies: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="parent_message",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<Message(id={self.id}, role='{self.role}', "
            f"conversation_id={self.conversation_id})>"
        )


class ConversationBookmark(BaseModel):
    """
    Bookmarked conversations for quick access.

    Allows users to save important conversations with custom names
    and personal notes for later reference.
    """

    __tablename__ = "conversation_bookmarks"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "conversation_id",
            name="uq_user_conversation_bookmark",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    conversation: Mapped["Conversation"] = relationship(
        "Conversation",
        back_populates="bookmarks",
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="bookmarks",
        lazy="select",
    )

    def __repr__(self) -> str:
        return (
            f"<ConversationBookmark(id={self.id}, "
            f"conversation_id={self.conversation_id}, "
            f"name='{self.name}')>"
        )


class MemoryEntry(BaseModel):
    """
    Long-term memory entries for user context.

    Stores different types of memories (conversation, semantic, factual,
    preference) with optional vector embeddings for similarity search.
    """

    __tablename__ = "memory_entries"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    memory_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    relevance_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )
    metadata_extra: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="memory_entries",
        lazy="select",
    )

    def __repr__(self) -> str:
        return (
            f"<MemoryEntry(id={self.id}, memory_type='{self.memory_type}', "
            f"user_id={self.user_id})>"
        )


class UserPreference(BaseModel):
    """
    User preference settings organized by category.

    Stores key-value pairs with JSONB values for flexible preference
    storage across different categories like LLM, UI, and notifications.
    """

    __tablename__ = "user_preferences"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "category",
            "key",
            name="uq_user_category_key",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    key: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    value: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="user_preferences",
        lazy="select",
    )

    def __repr__(self) -> str:
        return (
            f"<UserPreference(id={self.id}, category='{self.category}', "
            f"key='{self.key}')>"
        )
