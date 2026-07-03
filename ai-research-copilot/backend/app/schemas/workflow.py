"""
Workflow Pydantic v2 schemas.

Request/response schemas for workflow CRUD, execution, and monitoring.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class WorkflowCreate(BaseModel):
    """Schema for creating a new workflow."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Human-readable workflow name.",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=2048,
        description="Optional description of the workflow purpose and behavior.",
    )
    workflow_type: str = Field(
        ...,
        max_length=30,
        description="Workflow execution pattern (sequential, parallel, conditional, loop).",
    )
    definition: dict = Field(
        ...,
        description="Workflow graph structure with nodes and edges.",
    )
    is_template: bool = Field(
        default=False,
        description="Whether this workflow should be saved as a reusable template.",
    )


class WorkflowUpdate(BaseModel):
    """Schema for updating an existing workflow."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Updated workflow name.",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=2048,
        description="Updated workflow description.",
    )
    workflow_type: Optional[str] = Field(
        default=None,
        max_length=30,
        description="Updated workflow execution pattern.",
    )
    definition: Optional[dict] = Field(
        default=None,
        description="Updated workflow graph structure.",
    )
    status: Optional[str] = Field(
        default=None,
        max_length=30,
        description="Updated workflow status (draft, active, archived).",
    )
    is_template: Optional[bool] = Field(
        default=None,
        description="Updated template flag.",
    )


class WorkflowResponse(BaseModel):
    """Schema for workflow data returned in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    name: str
    workflow_type: str
    status: str
    is_template: bool
    execution_count: int
    created_at: datetime
    updated_at: datetime


class WorkflowDetail(WorkflowResponse):
    """Extended workflow schema with full definition and metadata."""

    description: Optional[str] = None
    definition: dict
    last_executed_at: Optional[datetime] = None
    metadata_extra: Optional[dict] = None


class WorkflowList(BaseModel):
    """Paginated list of workflows."""

    model_config = ConfigDict(from_attributes=True)

    items: list[WorkflowResponse]
    total: int
    page: int
    page_size: int


class WorkflowExecuteRequest(BaseModel):
    """Schema for executing a workflow."""

    model_config = ConfigDict(str_strip_whitespace=True)

    input_data: Optional[dict] = Field(
        default=None,
        description="Input data to pass to the workflow execution.",
    )


class WorkflowExecutionResponse(BaseModel):
    """Schema for workflow execution data returned in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workflow_id: UUID
    user_id: UUID
    status: str
    input_data: Optional[dict] = None
    output_data: Optional[dict] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    current_step: Optional[str] = None
    progress: float
    created_at: datetime


class WorkflowExecutionList(BaseModel):
    """Paginated list of workflow executions."""

    model_config = ConfigDict(from_attributes=True)

    items: list[WorkflowExecutionResponse]
    total: int


class WorkflowStepExecutionResponse(BaseModel):
    """Schema for individual workflow step execution data."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    execution_id: UUID
    step_name: str
    step_type: str
    status: str
    input_data: Optional[dict] = None
    output_data: Optional[dict] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    retry_count: int
