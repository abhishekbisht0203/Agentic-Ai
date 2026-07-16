"""
Database models package.

Exports all SQLAlchemy models for use throughout the application.
"""

from app.models.user import (
    APIKey,
    AuditLog,
    User,
    UserSession,
    UserRole,
    AuditLogStatus,
)
from app.models.document import (
    Document,
    DocumentChunk,
    KnowledgeBase,
    KnowledgeBaseDocument,
)
from app.models.conversation import (
    Conversation,
    Message,
    ConversationBookmark,
    MemoryEntry,
    UserPreference,
)
from app.models.workflow import (
    Workflow,
    WorkflowExecution,
    WorkflowStepExecution,
    AgentConfiguration,
    Task,
    WorkflowType,
    WorkflowStatus,
    ExecutionStatus,
    StepType,
    TaskType,
    TaskStatus,
)
from app.models.analytics import (
    AnalyticsReport,
    Visualization,
    UserActivity,
    ReportType,
    ReportStatus,
    DataSourceType,
    ChartType,
    ActivityType,
)
from app.models.llm_usage import (
    LLMRequest,
    LLMProvider,
    LLMRequestStatus,
)
from app.models.agent import (
    Agent,
    AgentRun,
    AgentMemory,
    AgentTool,
    AgentStatus,
    AgentVisibility,
)

__all__ = [
    # User models
    "User",
    "UserSession",
    "APIKey",
    "AuditLog",
    "UserRole",
    "AuditLogStatus",
    # Document models
    "Document",
    "DocumentChunk",
    "KnowledgeBase",
    "KnowledgeBaseDocument",
    # Conversation models
    "Conversation",
    "Message",
    "ConversationBookmark",
    "MemoryEntry",
    "UserPreference",
    # Workflow models
    "Workflow",
    "WorkflowExecution",
    "WorkflowStepExecution",
    "AgentConfiguration",
    "Task",
    "WorkflowType",
    "WorkflowStatus",
    "ExecutionStatus",
    "StepType",
    "TaskType",
    "TaskStatus",
    # Analytics models
    "AnalyticsReport",
    "Visualization",
    "UserActivity",
    "ReportType",
    "ReportStatus",
    "DataSourceType",
    "ChartType",
    "ActivityType",
    "LLMRequest",
    "LLMProvider",
    "LLMRequestStatus",
    "Agent",
    "AgentRun",
    "AgentMemory",
    "AgentTool",
    "AgentStatus",
    "AgentVisibility",
]
