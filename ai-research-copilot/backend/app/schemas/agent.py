"""
Agent configuration Pydantic v2 schemas.

Request/response schemas for agent configuration CRUD and execution.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AgentConfigurationCreate(BaseModel):
    """Schema for creating a new agent configuration."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Human-readable agent name.",
    )
    agent_type: str = Field(
        ...,
        max_length=50,
        description="Unique agent type identifier.",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=2048,
        description="Optional description of the agent purpose and capabilities.",
    )
    system_prompt: Optional[str] = Field(
        default=None,
        description="System prompt defining the agent behavior and instructions.",
    )
    model: Optional[str] = Field(
        default=None,
        max_length=100,
        description="LLM model identifier (e.g., gpt-4, claude-3-opus).",
    )
    temperature: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=2.0,
        description="Model temperature parameter controlling randomness (0.0-2.0).",
    )
    max_tokens: Optional[int] = Field(
        default=None,
        gt=0,
        description="Maximum number of tokens for model output.",
    )
    tools: Optional[list] = Field(
        default=None,
        description="List of tool names available to this agent.",
    )
    is_active: Optional[bool] = Field(
        default=True,
        description="Whether this agent configuration is active.",
    )


class AgentConfigurationUpdate(BaseModel):
    """Schema for updating an existing agent configuration."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Updated agent name.",
    )
    agent_type: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Updated agent type identifier.",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=2048,
        description="Updated agent description.",
    )
    system_prompt: Optional[str] = Field(
        default=None,
        description="Updated system prompt.",
    )
    model: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Updated LLM model identifier.",
    )
    temperature: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=2.0,
        description="Updated model temperature.",
    )
    max_tokens: Optional[int] = Field(
        default=None,
        gt=0,
        description="Updated maximum tokens for model output.",
    )
    tools: Optional[list] = Field(
        default=None,
        description="Updated list of tool names.",
    )
    is_active: Optional[bool] = Field(
        default=None,
        description="Updated active status.",
    )


class AgentConfigurationResponse(BaseModel):
    """Schema for agent configuration data returned in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    agent_type: str
    description: Optional[str] = None
    model: Optional[str] = None
    temperature: float
    max_tokens: int
    is_active: bool
    created_at: datetime


class AgentConfigurationDetail(AgentConfigurationResponse):
    """Extended agent configuration schema with full settings."""

    system_prompt: Optional[str] = None
    tools: Optional[list] = None
    metadata_extra: Optional[dict] = None


class AgentConfigurationList(BaseModel):
    """Paginated list of agent configurations."""

    model_config = ConfigDict(from_attributes=True)

    items: list[AgentConfigurationResponse]
    total: int


class AgentExecuteRequest(BaseModel):
    """Schema for executing an agent task."""

    model_config = ConfigDict(str_strip_whitespace=True)

    agent_type: str = Field(
        ...,
        max_length=50,
        description="Agent type identifier to execute.",
    )
    input_data: dict = Field(
        ...,
        description="Input data to process with the agent.",
    )
    conversation_id: Optional[UUID] = Field(
        default=None,
        description="Optional conversation ID for multi-turn interactions.",
    )
    model: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Optional model override for this execution.",
    )


class AgentExecuteResponse(BaseModel):
    """Schema for agent execution result."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    agent_type: str
    status: str
    output_data: Optional[dict] = None
    error_message: Optional[str] = None
    execution_time_ms: Optional[int] = None
