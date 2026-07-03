"""
Repository package.

Exports all repository classes for use throughout the application.
"""

from app.repositories.base import BaseRepository
from app.repositories.user import UserRepository
from app.repositories.document import DocumentRepository
from app.repositories.knowledge_base import KnowledgeBaseRepository
from app.repositories.conversation import ConversationRepository
from app.repositories.message import MessageRepository
from app.repositories.memory import (
    ConversationBookmarkRepository,
    MemoryEntryRepository,
    UserPreferenceRepository,
)
from app.repositories.workflow import WorkflowRepository
from app.repositories.analytics import (
    AnalyticsReportRepository,
    VisualizationRepository,
)
from app.repositories.task import TaskRepository

__all__ = [
    "BaseRepository",
    "UserRepository",
    "DocumentRepository",
    "KnowledgeBaseRepository",
    "ConversationRepository",
    "MessageRepository",
    "ConversationBookmarkRepository",
    "MemoryEntryRepository",
    "UserPreferenceRepository",
    "WorkflowRepository",
    "AnalyticsReportRepository",
    "VisualizationRepository",
    "TaskRepository",
]
