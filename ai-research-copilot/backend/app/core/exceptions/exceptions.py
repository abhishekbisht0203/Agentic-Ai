"""
Custom exception definitions for AI Research Copilot.

All application exceptions inherit from AIRCError for centralized error handling.
"""

from typing import Any


class AIRCError(Exception):
    """
    Base exception for all AI Research Copilot errors.

    All custom exceptions should inherit from this class to enable
    centralized error handling and logging.
    """

    def __init__(
        self,
        message: str = "An error occurred",
        code: str = "ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize the exception.

        Args:
            message: Human-readable error message.
            code: Error code for programmatic handling.
            details: Additional error details.
        """
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(AIRCError):
    """Raised when authentication fails or credentials are invalid."""

    def __init__(self, message: str = "Authentication failed", details: dict[str, Any] | None = None) -> None:
        super().__init__(message=message, code="AUTH_ERROR", details=details)


class AuthorizationError(AIRCError):
    """Raised when user lacks permission for an action."""

    def __init__(self, message: str = "Access denied", details: dict[str, Any] | None = None) -> None:
        super().__init__(message=message, code="FORBIDDEN", details=details)


class ValidationError(AIRCError):
    """Raised when input validation fails."""

    def __init__(self, message: str = "Validation failed", details: dict[str, Any] | None = None) -> None:
        super().__init__(message=message, code="VALIDATION_ERROR", details=details)


class NotFoundError(AIRCError):
    """Raised when a requested resource is not found."""

    def __init__(self, message: str = "Resource not found", details: dict[str, Any] | None = None) -> None:
        super().__init__(message=message, code="NOT_FOUND", details=details)


class DatabaseError(AIRCError):
    """Raised when a database operation fails."""

    def __init__(self, message: str = "Database operation failed", details: dict[str, Any] | None = None) -> None:
        super().__init__(message=message, code="DATABASE_ERROR", details=details)


class LLMError(AIRCError):
    """Raised when an LLM operation fails."""

    def __init__(self, message: str = "LLM operation failed", details: dict[str, Any] | None = None) -> None:
        super().__init__(message=message, code="LLM_ERROR", details=details)


class MCPError(AIRCError):
    """Raised when an MCP operation fails."""

    def __init__(self, message: str = "MCP operation failed", details: dict[str, Any] | None = None) -> None:
        super().__init__(message=message, code="MCP_ERROR", details=details)


class DocumentProcessingError(AIRCError):
    """Raised when document processing fails."""

    def __init__(self, message: str = "Document processing failed", details: dict[str, Any] | None = None) -> None:
        super().__init__(message=message, code="DOCUMENT_ERROR", details=details)


class WorkflowError(AIRCError):
    """Raised when workflow execution fails."""

    def __init__(self, message: str = "Workflow execution failed", details: dict[str, Any] | None = None) -> None:
        super().__init__(message=message, code="WORKFLOW_ERROR", details=details)