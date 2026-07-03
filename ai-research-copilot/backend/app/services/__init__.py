"""
Services package.

Exports all service classes for dependency injection.
"""

from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.services.document_service import DocumentService
from app.services.knowledge_base_service import KnowledgeBaseService
from app.services.chat_service import ChatService
from app.services.memory_service import MemoryService
from app.services.workflow_service import WorkflowService
from app.services.agent_service import AgentService
from app.services.analytics_service import AnalyticsService
from app.services.task_service import TaskService

__all__ = [
    "AuthService",
    "UserService",
    "DocumentService",
    "KnowledgeBaseService",
    "ChatService",
    "MemoryService",
    "WorkflowService",
    "AgentService",
    "AnalyticsService",
    "TaskService",
]
