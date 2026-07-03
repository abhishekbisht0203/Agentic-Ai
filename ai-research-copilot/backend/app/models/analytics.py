"""
Analytics-related SQLAlchemy models.

Defines AnalyticsReport, Visualization, and UserActivity models for tracking
data analysis workflows, generated visualizations, and user engagement metrics.
"""

import enum
import uuid

from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseModel


class ReportType(str, enum.Enum):
    """Enumeration of analytics report types."""

    EDA = "eda"
    STATISTICS = "statistics"
    REGRESSION = "regression"
    CLASSIFICATION = "classification"
    CLUSTERING = "clustering"
    FORECASTING = "forecasting"
    CUSTOM = "custom"


class ReportStatus(str, enum.Enum):
    """Enumeration of analytics report statuses."""

    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class DataSourceType(str, enum.Enum):
    """Enumeration of data source types for analytics."""

    DOCUMENT = "document"
    DATASET = "dataset"
    URL = "url"


class ChartType(str, enum.Enum):
    """Enumeration of visualization chart types."""

    LINE = "line"
    BAR = "bar"
    SCATTER = "scatter"
    HEATMAP = "heatmap"
    HISTOGRAM = "histogram"
    PIE = "pie"
    BOX = "box"
    AREA = "area"


class ActivityType(str, enum.Enum):
    """Enumeration of user activity types."""

    LOGIN = "login"
    CHAT = "chat"
    UPLOAD = "upload"
    AGENT_RUN = "agent_run"
    WORKFLOW_RUN = "workflow_run"


class AnalyticsReport(BaseModel):
    """Generated analytics report.

    Stores the full lifecycle of an analytics execution including input
    configuration, intermediate status, final results, and any errors
    encountered during generation.
    """

    __tablename__ = "analytics_reports"
    __table_args__ = (
        Index("ix_analytics_reports_user_id", "user_id"),
        Index("ix_analytics_reports_report_type", "report_type"),
        Index("ix_analytics_reports_status", "status"),
        Index("ix_analytics_reports_data_source", "data_source_type", "data_source_id"),
        {"comment": "Generated analytics reports"},
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to the user who requested the report",
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Human-readable report name",
    )
    report_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Type of analysis performed",
    )
    status: Mapped[str] = mapped_column(
        String(30),
        default=ReportStatus.PENDING,
        nullable=False,
        comment="Current report generation status",
    )
    input_config: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        comment="Analysis parameters and input configuration",
    )
    results: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Analysis results output",
    )
    file_path: Mapped[str | None] = mapped_column(
        String(1024),
        nullable=True,
        comment="Path to exported report file on storage",
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Error message if report generation failed",
    )
    data_source_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Type of data source (document, dataset, url)",
    )
    data_source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="ID of the data source used for analysis",
    )
    execution_time_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Total execution time in milliseconds",
    )
    extra_metadata: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Additional report metadata",
    )

    visualizations: Mapped[list["Visualization"]] = relationship(
        "Visualization",
        back_populates="report",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="analytics_reports",
    )

    def __repr__(self) -> str:
        return (
            f"<AnalyticsReport(id={self.id}, name={self.name}, "
            f"report_type={self.report_type}, status={self.status})>"
        )


class Visualization(BaseModel):
    """Generated chart or visualization.

    Stores chart configuration, rendering output, and optional linkage
    to an AnalyticsReport for grouping related visualizations together.
    """

    __tablename__ = "visualizations"
    __table_args__ = (
        Index("ix_visualizations_user_id", "user_id"),
        Index("ix_visualizations_report_id", "report_id"),
        Index("ix_visualizations_chart_type", "chart_type"),
        {"comment": "Generated charts and visualizations"},
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to the user who created the visualization",
    )
    report_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analytics_reports.id", ondelete="SET NULL"),
        nullable=True,
        comment="Reference to the parent analytics report",
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Human-readable visualization name",
    )
    chart_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Type of chart rendered",
    )
    config: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        comment="Chart configuration and data payload",
    )
    image_path: Mapped[str | None] = mapped_column(
        String(1024),
        nullable=True,
        comment="Path to rendered chart image on storage",
    )
    extra_metadata: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Additional visualization metadata",
    )

    report: Mapped["AnalyticsReport | None"] = relationship(
        "AnalyticsReport",
        back_populates="visualizations",
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="visualizations",
    )

    def __repr__(self) -> str:
        return (
            f"<Visualization(id={self.id}, name={self.name}, "
            f"chart_type={self.chart_type})>"
        )


class UserActivity(BaseModel):
    """User activity tracking record.

    Captures a log of user interactions across the platform including
    logins, chat sessions, file uploads, and agent/workflow executions.
    """

    __tablename__ = "user_activities"
    __table_args__ = (
        Index("ix_user_activities_user_id", "user_id"),
        Index("ix_user_activities_activity_type", "activity_type"),
        Index("ix_user_activities_resource", "resource_type", "resource_id"),
        Index("ix_user_activities_created_at", "created_at"),
        {"comment": "User activity tracking log"},
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to the user who performed the activity",
    )
    activity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Type of activity performed",
    )
    resource_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Type of resource involved in the activity",
    )
    resource_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="ID of the resource involved in the activity",
    )
    extra_metadata: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Additional activity context and metadata",
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="activities",
    )

    def __repr__(self) -> str:
        return (
            f"<UserActivity(id={self.id}, user_id={self.user_id}, "
            f"activity_type={self.activity_type})>"
        )
