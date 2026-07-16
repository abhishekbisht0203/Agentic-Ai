
import enum
from datetime import datetime, timezone
from sqlalchemy import BigInteger, Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.database.base import BaseModel


class LLMProvider(str, enum.Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    GROQ = "groq"
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"
    OPENCODE = "opencode"


class LLMRequestStatus(str, enum.Enum):
    SUCCESS = "success"
    FAILED = "failed"
    STREAMING = "streaming"
    CACHED = "cached"


class LLMRequest(BaseModel):
    __tablename__ = "llm_requests"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True, index=True)
    agent_type = Column(String(100), nullable=True, index=True)

    provider = Column(String(50), nullable=False, index=True)
    model = Column(String(200), nullable=False, index=True)
    request_type = Column(String(50), default="chat", index=True)

    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)

    cost_usd = Column(Float(precision=10), default=0.0)
    duration_ms = Column(Integer, default=0)

    status = Column(String(20), default="success", index=True)
    error_message = Column(Text, nullable=True)
    cached = Column(Integer, default=0)
    streaming = Column(Integer, default=0)

    metadata_ = Column("metadata", JSONB, nullable=True)

    requested_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
