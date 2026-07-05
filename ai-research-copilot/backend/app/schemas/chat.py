"""
Chat and conversation Pydantic v2 schemas.

Request/response schemas for conversations, messages, bookmarks,
and real-time chat streaming events.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ConversationCreate(BaseModel):
    """Schema for creating a new conversation."""

    model_config = ConfigDict(str_strip_whitespace=True)

    title: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Human-readable conversation title. Auto-generated if omitted.",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=1024,
        description="Optional description summarizing the conversation topic.",
    )
    agent_type: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Type of agent to use (e.g. 'research', 'general', 'coding').",
    )
    knowledge_base_id: Optional[UUID] = Field(
        default=None,
        description="Knowledge base ID to scope retrieval-augmented responses.",
    )


class ConversationUpdate(BaseModel):
    """Schema for updating an existing conversation."""

    model_config = ConfigDict(str_strip_whitespace=True)

    title: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Updated conversation title.",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=1024,
        description="Updated conversation description.",
    )
    status: Optional[str] = Field(
        default=None,
        max_length=30,
        description="Conversation status (e.g. 'active', 'archived', 'closed').",
    )

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str | None) -> str | None:
        """Validate the conversation status is a recognised value."""
        if v is None:
            return v
        allowed = {"active", "archived", "closed"}
        if v not in allowed:
            raise ValueError(f"Status must be one of {sorted(allowed)}")
        return v


class MessageCreate(BaseModel):
    """Schema for adding a message to a conversation."""

    model_config = ConfigDict(str_strip_whitespace=True)

    content: str = Field(
        ...,
        min_length=1,
        description="The message body text.",
    )
    role: str = Field(
        default="user",
        max_length=20,
        description="Message role ('user', 'assistant', or 'system').",
    )

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Validate the message role is a recognised value."""
        allowed = {"user", "assistant", "system"}
        if v not in allowed:
            raise ValueError(f"Role must be one of {sorted(allowed)}")
        return v


class MessageResponse(BaseModel):
    """Schema for a single message returned in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    conversation_id: UUID
    role: str
    content: str
    model_used: Optional[str] = None
    token_count: Optional[int] = None
    agent_type: Optional[str] = None
    tool_calls: Optional[list] = None
    citations: Optional[list] = None
    metadata: Optional[dict] = Field(
        default=None,
        validation_alias="metadata_extra",
    )
    created_at: datetime
    updated_at: datetime


class MessageList(BaseModel):
    """Paginated list of messages."""

    model_config = ConfigDict(from_attributes=True)

    items: list[MessageResponse]
    total: int


class ConversationResponse(BaseModel):
    """Schema for conversation data returned in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    title: Optional[str] = None
    description: Optional[str] = None
    agent_type: Optional[str] = None
    model_used: Optional[str] = None
    status: str
    message_count: int
    knowledge_base_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime


class ConversationDetail(ConversationResponse):
    """Extended conversation schema with messages and context details."""

    messages: list[MessageResponse] = Field(default_factory=list)
    token_usage: Optional[dict] = None
    metadata_extra: Optional[dict] = None


class ConversationList(BaseModel):
    """Paginated list of conversations."""

    model_config = ConfigDict(from_attributes=True)

    items: list[ConversationResponse]
    total: int
    page: int
    page_size: int


class ChatRequest(BaseModel):
    """Schema for sending a chat message and receiving a response."""

    model_config = ConfigDict(str_strip_whitespace=True)

    message: str = Field(
        ...,
        min_length=1,
        description="The user message to send.",
    )
    conversation_id: Optional[UUID] = Field(
        default=None,
        description="Conversation to continue. A new conversation is created when omitted.",
    )
    agent_type: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Override the conversation's default agent type.",
    )
    model: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Specific LLM model identifier to use for this turn.",
    )
    knowledge_base_id: Optional[UUID] = Field(
        default=None,
        description="Knowledge base ID for retrieval-augmented generation.",
    )
    stream: bool = Field(
        default=False,
        description="When true the response is delivered via server-sent events.",
    )


class ChatResponse(BaseModel):
    """Schema for a completed chat response."""

    model_config = ConfigDict(from_attributes=True)

    conversation_id: UUID
    message: MessageResponse
    citations: list[Any] = Field(default_factory=list)


class ChatStreamEvent(BaseModel):
    """Schema for a single server-sent event during streaming."""

    model_config = ConfigDict(from_attributes=True)

    event: str = Field(
        ...,
        description="Event type: 'message', 'error', 'citation', or 'done'.",
    )
    data: dict = Field(
        default_factory=dict,
        description="Event payload. Shape depends on the event type.",
    )

    @field_validator("event")
    @classmethod
    def validate_event(cls, v: str) -> str:
        """Validate the event type is a recognised value."""
        allowed = {"message", "error", "citation", "done"}
        if v not in allowed:
            raise ValueError(f"Event must be one of {sorted(allowed)}")
        return v


class ConversationBookmarkCreate(BaseModel):
    """Schema for creating a bookmark on a conversation."""

    model_config = ConfigDict(str_strip_whitespace=True)

    conversation_id: UUID = Field(
        ...,
        description="Conversation to bookmark.",
    )
    name: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Optional short label for the bookmark.",
    )
    note: Optional[str] = Field(
        default=None,
        description="Optional personal note attached to the bookmark.",
    )


class ConversationBookmarkResponse(BaseModel):
    """Schema for a bookmark returned in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    conversation_id: UUID
    name: Optional[str] = None
    note: Optional[str] = None
    created_at: datetime
