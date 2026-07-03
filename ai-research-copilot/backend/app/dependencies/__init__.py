"""
Dependency injection module for FastAPI.

Provides reusable dependencies for authentication, authorization,
database sessions, and other cross-cutting concerns.
"""

from app.dependencies.auth import (
    get_current_user_from_token,
    require_permission,
    require_role,
)

__all__ = [
    "get_current_user_from_token",
    "require_permission",
    "require_role",
]
