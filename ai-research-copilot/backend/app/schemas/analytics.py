"""
Analytics Pydantic v2 schemas.

Request/response schemas for analytics reports, visualizations,
user activity tracking, and summary dashboards.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AnalyticsReportCreate(BaseModel):
    """Schema for creating a new analytics report."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Human-readable report name.",
    )
    report_type: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Type of analytics report (e.g. 'usage', 'performance', 'trend').",
    )
    input_config: dict = Field(
        ...,
        description="Configuration parameters for the report generation.",
    )
    data_source_type: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Type of data source (e.g. 'document', 'knowledge_base', 'api').",
    )
    data_source_id: Optional[UUID] = Field(
        default=None,
        description="UUID of the specific data source to query.",
    )


class AnalyticsReportResponse(BaseModel):
    """Schema for analytics report data returned in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    name: str
    report_type: str
    status: str
    input_config: dict
    results: Optional[dict] = None
    error_message: Optional[str] = None
    data_source_type: Optional[str] = None
    data_source_id: Optional[UUID] = None
    execution_time_ms: Optional[float] = None
    created_at: datetime
    updated_at: datetime


class AnalyticsReportList(BaseModel):
    """Paginated list of analytics reports."""

    model_config = ConfigDict(from_attributes=True)

    items: list[AnalyticsReportResponse]
    total: int
    page: int
    page_size: int


class VisualizationCreate(BaseModel):
    """Schema for creating a new visualization."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Human-readable visualization name.",
    )
    chart_type: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Type of chart (e.g. 'bar', 'line', 'pie', 'scatter', 'heatmap').",
    )
    config: dict = Field(
        ...,
        description="Chart configuration (axes, colors, labels, etc.).",
    )
    report_id: Optional[UUID] = Field(
        default=None,
        description="UUID of the analytics report this visualization is derived from.",
    )


class VisualizationResponse(BaseModel):
    """Schema for visualization data returned in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    report_id: Optional[UUID] = None
    name: str
    chart_type: str
    config: dict
    image_path: Optional[str] = None
    created_at: datetime


class VisualizationList(BaseModel):
    """List of visualizations."""

    model_config = ConfigDict(from_attributes=True)

    items: list[VisualizationResponse]
    total: int


class UserActivityResponse(BaseModel):
    """Schema for a single user activity record."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    activity_type: str
    resource_type: Optional[str] = None
    resource_id: Optional[UUID] = None
    extra_metadata: Optional[dict] = None
    created_at: datetime


class UserActivityList(BaseModel):
    """List of user activity records."""

    model_config = ConfigDict(from_attributes=True)

    items: list[UserActivityResponse]
    total: int


class AnalyticsSummary(BaseModel):
    """Aggregated analytics summary for a user or tenant dashboard."""

    model_config = ConfigDict(from_attributes=True)

    total_reports: int = Field(
        ...,
        ge=0,
        description="Total number of analytics reports.",
    )
    total_visualizations: int = Field(
        ...,
        ge=0,
        description="Total number of visualizations created.",
    )
    activity_count: int = Field(
        ...,
        ge=0,
        description="Total number of tracked activity events.",
    )
    reports_by_type: dict = Field(
        ...,
        description="Mapping of report type to its count (e.g. {'usage': 5, 'trend': 3}).",
    )
    recent_activities: list = Field(
        ...,
        description="Most recent activity records (up to 10).",
    )
