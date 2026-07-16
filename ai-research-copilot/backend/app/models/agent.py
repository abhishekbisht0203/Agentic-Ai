
import enum
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.database.base import BaseModel


class AgentStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"


class AgentVisibility(str, enum.Enum):
    PRIVATE = "private"
    PUBLIC = "public"


class Agent(BaseModel):
    __tablename__ = "agents"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    system_prompt = Column(Text, nullable=True)
    avatar = Column(String(100), nullable=True)
    icon = Column(String(50), default="Bot")
    color = Column(String(7), default="#6366f1")
    model = Column(String(100), default="openai/gpt-oss-120b:free")
    provider = Column(String(50), default="openrouter")
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=4096)
    top_p = Column(Float, default=1.0)
    frequency_penalty = Column(Float, default=0.0)
    presence_penalty = Column(Float, default=0.0)
    tools_enabled = Column(JSONB, nullable=True)
    knowledge_base_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_bases.id", ondelete="SET NULL"), nullable=True)
    memory_enabled = Column(Boolean, default=False)
    rag_enabled = Column(Boolean, default=False)
    workflow_enabled = Column(Boolean, default=False)
    status = Column(String(20), default="active")
    visibility = Column(String(20), default="private")


class AgentRun(BaseModel):
    __tablename__ = "agent_runs"

    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True)
    input_text = Column(Text, nullable=True)
    output_text = Column(Text, nullable=True)
    tokens_prompt = Column(Integer, default=0)
    tokens_completion = Column(Integer, default=0)
    tokens_total = Column(Integer, default=0)
    latency_ms = Column(Integer, default=0)
    cost_usd = Column(Float, default=0.0)
    success = Column(Boolean, default=True)
    error = Column(Text, nullable=True)
    model_used = Column(String(100), nullable=True)
    provider_used = Column(String(50), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)


class AgentMemory(BaseModel):
    __tablename__ = "agent_memory"

    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    key = Column(String(255), nullable=False)
    value = Column(Text, nullable=False)
    memory_type = Column(String(50), default="fact")
    relevance_score = Column(Float, default=1.0)
    expires_at = Column(DateTime(timezone=True), nullable=True)


class AgentTool(BaseModel):
    __tablename__ = "agent_tools"

    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    tool_name = Column(String(100), nullable=False)
    enabled = Column(Boolean, default=True)
    config = Column(JSONB, nullable=True)
