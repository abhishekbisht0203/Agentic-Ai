"""
Task Pydantic v2 schemas.

Request/response schemas for background task monitoring and management.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TaskResponse(BaseModel):
    """Schema for task data returned in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    task_type: str
    status: str
    priority: int
    input_data: Optional[dict] = None
    output_data: Optional[dict] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    celery_task_id: Optional[str] = None
    retry_count: int
    created_at: datetime


class TaskList(BaseModel):
    """Paginated list of tasks."""

    model_config = ConfigDict(from_attributes=True)

    items: list[TaskResponse]
    total: int


class TaskCancelRequest(BaseModel):
    """Schema for cancelling a running task."""

    model_config = ConfigDict(str_strip_whitespace=True)

    task_id: UUID = Field(
        ...,
        description="UUID of the task to cancel.",
    )
