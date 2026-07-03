"""
Workflow-related SQLAlchemy models.

Defines Workflow, WorkflowExecution, WorkflowStepExecution,
AgentConfiguration, and Task models for workflow orchestration
and background task management.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseModel


class WorkflowType(str, enum.Enum):
    """Enumeration of workflow types."""

    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    LOOP = "loop"


class WorkflowStatus(str, enum.Enum):
    """Enumeration of workflow statuses."""

    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class ExecutionStatus(str, enum.Enum):
    """Enumeration of execution statuses."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    WAITING_APPROVAL = "waiting_approval"


class StepType(str, enum.Enum):
    """Enumeration of workflow step types."""

    AGENT_CALL = "agent_call"
    TOOL_CALL = "tool_call"
    CONDITION = "condition"
    WAIT = "wait"
    APPROVAL = "approval"


class TaskType(str, enum.Enum):
    """Enumeration of background task types."""

    DOCUMENT_PROCESSING = "document_processing"
    EMBEDDING = "embedding"
    WORKFLOW = "workflow"
    AGENT = "agent"
    DATA_EXPORT = "data_export"
    REPORT_GENERATION = "report_generation"
    NOTIFICATION = "notification"


class TaskStatus(str, enum.Enum):
    """Enumeration of task statuses."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRY = "retry"


class Workflow(BaseModel):
    """Workflow definition model.

    Stores workflow configurations including the graph structure
    (nodes and edges), execution metadata, and template support.
    """

    __tablename__ = "workflows"
    __table_args__ = (
        Index("ix_workflows_user_id", "user_id"),
        Index("ix_workflows_name", "name"),
        Index("ix_workflows_status", "status"),
        Index("ix_workflows_workflow_type", "workflow_type"),
        {"comment": "Workflow definitions"},
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to the owner user",
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Workflow name",
    )
    description: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True,
        comment="Workflow description",
    )
    workflow_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=WorkflowType.SEQUENTIAL,
        comment="Workflow execution pattern (sequential, parallel, conditional, loop)",
    )
    definition: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Workflow graph structure with nodes and edges",
    )
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=WorkflowStatus.DRAFT,
        comment="Workflow status (draft, active, archived)",
    )
    is_template: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether this workflow is a reusable template",
    )
    execution_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of times this workflow has been executed",
    )
    last_executed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of last execution",
    )
    metadata_extra: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Additional metadata stored as JSON",
    )

    executions: Mapped[list["WorkflowExecution"]] = relationship(
        "WorkflowExecution",
        back_populates="workflow",
        cascade="all, delete-orphan",
        lazy="noload",
    )

    def __repr__(self) -> str:
        return (
            f"<Workflow(id={self.id}, name={self.name}, "
            f"status={self.status}, type={self.workflow_type})>"
        )


class WorkflowExecution(BaseModel):
    """Workflow execution instance model.

    Tracks individual runs of a workflow including input/output data,
    progress, and timing information.
    """

    __tablename__ = "workflow_executions"
    __table_args__ = (
        Index("ix_workflow_executions_workflow_id", "workflow_id"),
        Index("ix_workflow_executions_user_id", "user_id"),
        Index("ix_workflow_executions_status", "status"),
        Index("ix_workflow_executions_created_at", "created_at"),
        {"comment": "Running and completed workflow instances"},
    )

    workflow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to the workflow definition",
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to the user who initiated execution",
    )
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=ExecutionStatus.PENDING,
        comment="Execution status (pending, running, completed, failed, cancelled, waiting_approval)",
    )
    input_data: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Input data for the workflow execution",
    )
    output_data: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Output data from the completed workflow",
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Error message if execution failed",
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when execution started",
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when execution completed",
    )
    duration_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Execution duration in milliseconds",
    )
    current_step: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Name of the currently executing step",
    )
    progress: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        comment="Execution progress percentage (0-100)",
    )

    workflow: Mapped["Workflow"] = relationship(
        "Workflow",
        back_populates="executions",
    )
    step_executions: Mapped[list["WorkflowStepExecution"]] = relationship(
        "WorkflowStepExecution",
        back_populates="execution",
        cascade="all, delete-orphan",
        lazy="noload",
    )

    def __repr__(self) -> str:
        return (
            f"<WorkflowExecution(id={self.id}, workflow_id={self.workflow_id}, "
            f"status={self.status})>"
        )


class WorkflowStepExecution(BaseModel):
    """Individual step execution within a workflow run.

    Tracks execution details for each step including timing,
    retry logic, and checkpoint data for resumability.
    """

    __tablename__ = "workflow_step_executions"
    __table_args__ = (
        Index("ix_workflow_step_executions_execution_id", "execution_id"),
        Index("ix_workflow_step_executions_status", "status"),
        Index("ix_workflow_step_executions_step_type", "step_type"),
        {"comment": "Individual step executions within workflow runs"},
    )

    execution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflow_executions.id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to the parent workflow execution",
    )
    step_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Name identifier of the workflow step",
    )
    step_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Type of step (agent_call, tool_call, condition, wait, approval)",
    )
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=ExecutionStatus.PENDING,
        comment="Step execution status (pending, running, completed, failed, skipped, waiting_approval)",
    )
    input_data: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Input data passed to the step",
    )
    output_data: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Output data produced by the step",
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Error message if step failed",
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when step execution started",
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when step execution completed",
    )
    duration_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Step execution duration in milliseconds",
    )
    agent_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Type of agent used (for agent_call steps)",
    )
    retry_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of retry attempts for this step",
    )
    checkpoint_data: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Checkpoint data for step resumability",
    )

    execution: Mapped["WorkflowExecution"] = relationship(
        "WorkflowExecution",
        back_populates="step_executions",
    )

    def __repr__(self) -> str:
        return (
            f"<WorkflowStepExecution(id={self.id}, step_name={self.step_name}, "
            f"status={self.status})>"
        )


class AgentConfiguration(BaseModel):
    """Agent configuration and definition model.

    Stores agent settings including model parameters, system prompts,
    and available tools for each agent type.
    """

    __tablename__ = "agent_configurations"
    __table_args__ = (
        Index("ix_agent_configurations_name", "name"),
        Index("ix_agent_configurations_agent_type", "agent_type", unique=True),
        {"comment": "Agent configuration and definitions"},
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Human-readable agent name",
    )
    agent_type: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        comment="Unique agent type identifier",
    )
    description: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True,
        comment="Agent description and purpose",
    )
    system_prompt: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="System prompt for the agent",
    )
    model: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="LLM model identifier",
    )
    temperature: Mapped[float] = mapped_column(
        Float,
        default=0.7,
        nullable=False,
        comment="Model temperature parameter (0.0-2.0)",
    )
    max_tokens: Mapped[int] = mapped_column(
        Integer,
        default=4096,
        nullable=False,
        comment="Maximum tokens for model output",
    )
    tools: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="List of tool names available to this agent",
    )
    metadata_extra: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Additional agent configuration stored as JSON",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether this agent configuration is active",
    )

    def __repr__(self) -> str:
        return (
            f"<AgentConfiguration(id={self.id}, name={self.name}, "
            f"agent_type={self.agent_type})>"
        )


class Task(BaseModel):
    """Background task tracking model.

    Monitors long-running background operations including document
    processing, embedding generation, and workflow executions.
    """

    __tablename__ = "tasks"
    __table_args__ = (
        Index("ix_tasks_user_id", "user_id"),
        Index("ix_tasks_task_type", "task_type"),
        Index("ix_tasks_status", "status"),
        Index("ix_tasks_celery_task_id", "celery_task_id"),
        Index("ix_tasks_priority", "priority"),
        {"comment": "Background task tracking"},
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to the user who initiated the task",
    )
    task_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Type of task (document_processing, embedding, workflow, agent, etc.)",
    )
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=TaskStatus.PENDING,
        comment="Task status (pending, running, completed, failed, cancelled, retry)",
    )
    priority: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Task priority (higher values = higher priority)",
    )
    input_data: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Input data for the task",
    )
    output_data: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Output data from the completed task",
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Error message if task failed",
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when task execution started",
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when task execution completed",
    )
    celery_task_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Celery task ID for async task tracking",
    )
    retry_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of retry attempts",
    )
    max_retries: Mapped[int] = mapped_column(
        Integer,
        default=3,
        nullable=False,
        comment="Maximum allowed retry attempts",
    )
    metadata_extra: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Additional task metadata stored as JSON",
    )

    def __repr__(self) -> str:
        return (
            f"<Task(id={self.id}, task_type={self.task_type}, "
            f"status={self.status}, priority={self.priority})>"
        )
