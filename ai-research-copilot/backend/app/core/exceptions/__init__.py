"""
Core exception definitions.

Provides custom exceptions for the AI Research Copilot application.
"""

from .exceptions import (
    AIRCError,
    AuthenticationError,
    AuthorizationError,
    DatabaseError,
    DocumentProcessingError,
    LLMError,
    MCPError,
    NotFoundError,
    ValidationError,
    WorkflowError,
)

__all__ = [
    "AIRCError",
    "AuthenticationError",
    "AuthorizationError",
    "DatabaseError",
    "DocumentProcessingError",
    "LLMError",
    "MCPError",
    "NotFoundError",
    "ValidationError",
    "WorkflowError",
]