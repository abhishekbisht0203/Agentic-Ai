
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AgentCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    avatar: Optional[str] = None
    icon: str = "Bot"
    color: str = "#6366f1"
    model: str = "openai/gpt-oss-120b:free"
    provider: str = "openrouter"
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    tools_enabled: Optional[list[str]] = None
    knowledge_base_id: Optional[UUID] = None
    memory_enabled: bool = False
    rag_enabled: bool = False
    workflow_enabled: bool = False
    status: str = "active"
    visibility: str = "private"


class AgentUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    avatar: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    model: Optional[str] = None
    provider: Optional[str] = None
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    tools_enabled: Optional[list[str]] = None
    knowledge_base_id: Optional[UUID] = None
    memory_enabled: Optional[bool] = None
    rag_enabled: Optional[bool] = None
    workflow_enabled: Optional[bool] = None
    status: Optional[str] = None
    visibility: Optional[str] = None


class AgentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    name: str
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    avatar: Optional[str] = None
    icon: str
    color: str
    model: str
    provider: str
    temperature: float
    max_tokens: int
    top_p: float
    frequency_penalty: float
    presence_penalty: float
    tools_enabled: Optional[list] = None
    knowledge_base_id: Optional[UUID] = None
    memory_enabled: bool
    rag_enabled: bool
    workflow_enabled: bool
    status: str
    visibility: str
    created_at: datetime
    updated_at: datetime


class AgentWithStats(AgentResponse):
    total_runs: int = 0
    last_run_at: Optional[datetime] = None
    avg_latency_ms: float = 0.0
    success_rate: float = 0.0
    total_tokens: int = 0
    total_cost: float = 0.0
    active_conversations: int = 0


class AgentList(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[AgentWithStats]
    total: int


class AgentRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    agent_id: UUID
    conversation_id: Optional[UUID] = None
    input_text: Optional[str] = None
    output_text: Optional[str] = None
    tokens_prompt: int = 0
    tokens_completion: int = 0
    tokens_total: int = 0
    latency_ms: int = 0
    cost_usd: float = 0.0
    success: bool
    error: Optional[str] = None
    model_used: Optional[str] = None
    provider_used: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime


class AgentRunList(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[AgentRunResponse]
    total: int


class AgentMemoryCreate(BaseModel):
    key: str = Field(..., max_length=255)
    value: str = Field(...)
    memory_type: str = "fact"
    relevance_score: float = 1.0


class AgentMemoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    agent_id: UUID
    key: str
    value: str
    memory_type: str
    relevance_score: float
    created_at: datetime


class AgentToolCreate(BaseModel):
    tool_name: str = Field(..., max_length=100)
    enabled: bool = True
    config: Optional[dict] = None


class AgentToolResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    agent_id: UUID
    tool_name: str
    enabled: bool
    config: Optional[dict] = None


class AgentChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    conversation_id: Optional[UUID] = None


class AgentChatResponse(BaseModel):
    conversation_id: UUID
    message: str
    role: str = "assistant"


class AgentDuplicate(BaseModel):
    name: Optional[str] = None
