"""
Common/shared Pydantic v2 schemas.

Reusable schemas for pagination, sorting, filtering,
standard API responses, health checks, and metrics.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class PaginationParams(BaseModel):
    """Query parameters for paginated list endpoints."""

    model_config = ConfigDict(str_strip_whitespace=True)

    page: int = Field(
        default=1,
        ge=1,
        description="Page number (1-indexed).",
    )
    page_size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Number of items per page.",
    )


class SortParams(BaseModel):
    """Query parameters for sorting list results."""

    model_config = ConfigDict(str_strip_whitespace=True)

    sort_by: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Field name to sort by (e.g. 'created_at', 'name').",
    )
    sort_order: Optional[str] = Field(
        default=None,
        pattern=r"^(asc|desc)$",
        description="Sort direction: 'asc' for ascending, 'desc' for descending.",
    )


class FilterParams(BaseModel):
    """Query parameters for filtering list results."""

    model_config = ConfigDict(str_strip_whitespace=True)

    search: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Free-text search query.",
    )
    status: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Filter by status value (e.g. 'active', 'archived').",
    )
    created_after: Optional[datetime] = Field(
        default=None,
        description="Return items created on or after this datetime.",
    )
    created_before: Optional[datetime] = Field(
        default=None,
        description="Return items created on or before this datetime.",
    )


class ErrorDetail(BaseModel):
    """Structured error information."""

    model_config = ConfigDict(from_attributes=True)

    code: str = Field(
        ...,
        max_length=100,
        description="Machine-readable error code (e.g. 'NOT_FOUND', 'VALIDATION_ERROR').",
    )
    message: str = Field(
        ...,
        description="Human-readable error message.",
    )
    details: Optional[dict] = Field(
        default=None,
        description="Additional context about the error.",
    )


class SuccessResponse(BaseModel):
    """Standard success response envelope."""

    model_config = ConfigDict(from_attributes=True)

    message: str = Field(
        ...,
        description="Confirmation or status message.",
    )
    data: Optional[dict] = Field(
        default=None,
        description="Optional payload returned with the success response.",
    )


class ErrorResponse(BaseModel):
    """Standard error response envelope."""

    model_config = ConfigDict(from_attributes=True)

    error: ErrorDetail = Field(
        ...,
        description="Structured error detail.",
    )


class HealthCheckResponse(BaseModel):
    """Health check response with service statuses."""

    model_config = ConfigDict(from_attributes=True)

    status: str = Field(
        ...,
        description="Overall health status (e.g. 'healthy', 'degraded', 'unhealthy').",
    )
    version: str = Field(
        ...,
        description="Application version string.",
    )
    database: str = Field(
        ...,
        description="Database connection status (e.g. 'connected', 'disconnected').",
    )
    redis: str = Field(
        ...,
        description="Redis connection status (e.g. 'connected', 'disconnected').",
    )
    qdrant: str = Field(
        ...,
        description="Qdrant vector DB connection status (e.g. 'connected', 'disconnected').",
    )
    uptime: float = Field(
        ...,
        ge=0.0,
        description="Server uptime in seconds.",
    )


class MetricsResponse(BaseModel):
    """System-wide metrics summary."""

    model_config = ConfigDict(from_attributes=True)

    total_users: int = Field(
        ...,
        ge=0,
        description="Total registered users.",
    )
    total_documents: int = Field(
        ...,
        ge=0,
        description="Total documents across all knowledge bases.",
    )
    total_conversations: int = Field(
        ...,
        ge=0,
        description="Total conversations started.",
    )
    total_workflows: int = Field(
        ...,
        ge=0,
        description="Total workflows created.",
    )
    storage_used_bytes: int = Field(
        ...,
        ge=0,
        description="Total storage consumed in bytes.",
    )
