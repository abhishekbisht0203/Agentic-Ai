"""
Role-based access control (RBAC) and permissions.

Provides permission checking decorators and role definitions.
"""

from enum import Enum
from functools import wraps
from typing import Any, Callable

from app.core.exceptions import AuthorizationError


class Role(str, Enum):
    """User roles for RBAC."""

    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"
    GUEST = "guest"


class Permission(str, Enum):
    """Available permissions in the system."""

    # User management
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    USER_DELETE = "user:delete"

    # Document management
    DOCUMENT_READ = "document:read"
    DOCUMENT_WRITE = "document:write"
    DOCUMENT_DELETE = "document:delete"

    # Agent management
    AGENT_EXECUTE = "agent:execute"
    AGENT_CONFIGURE = "agent:configure"

    # Workflow management
    WORKFLOW_CREATE = "workflow:create"
    WORKFLOW_EXECUTE = "workflow:execute"
    WORKFLOW_CANCEL = "workflow:cancel"

    # MCP tools
    MCP_TOOL_USE = "mcp:tool-use"
    MCP_TOOL_CONFIGURE = "mcp:tool-configure"

    # Analytics
    ANALYTICS_READ = "analytics:read"
    ANALYTICS_WRITE = "analytics:write"

    # All permissions
    ALL = "*"


# Role to permission mapping
ROLE_PERMISSIONS: dict[Role, list[Permission]] = {
    Role.ADMIN: [Permission.ALL],
    Role.USER: [
        Permission.USER_READ,
        Permission.USER_WRITE,
        Permission.DOCUMENT_READ,
        Permission.DOCUMENT_WRITE,
        Permission.DOCUMENT_DELETE,
        Permission.AGENT_EXECUTE,
        Permission.AGENT_CONFIGURE,
        Permission.WORKFLOW_CREATE,
        Permission.WORKFLOW_EXECUTE,
        Permission.WORKFLOW_CANCEL,
        Permission.MCP_TOOL_USE,
        Permission.ANALYTICS_READ,
        Permission.ANALYTICS_WRITE,
    ],
    Role.VIEWER: [
        Permission.USER_READ,
        Permission.DOCUMENT_READ,
        Permission.ANALYTICS_READ,
    ],
    Role.GUEST: [
        Permission.USER_READ,
        Permission.DOCUMENT_READ,
    ],
}


def get_permissions_for_role(role: Role) -> list[Permission]:
    """
    Get all permissions for a given role.

    Args:
        role: User role.

    Returns:
        List of permissions granted to the role.
    """
    return ROLE_PERMISSIONS.get(role, [])


def has_permission(role: Role, permission: Permission) -> bool:
    """
    Check if a role has a specific permission.

    Args:
        role: User role to check.
        permission: Permission to verify.

    Returns:
        True if role has permission, False otherwise.
    """
    if permission == Permission.ALL:
        return True

    role_permissions = get_permissions_for_role(role)
    return Permission.ALL in role_permissions or permission in role_permissions


def permission_required(permission: Permission) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator to require a specific permission for an endpoint.

    Args:
        permission: Required permission.

    Returns:
        Decorated function that checks permissions.

    Raises:
        AuthorizationError: If user lacks required permission.
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Extract user from kwargs or use default
            user: dict[str, Any] | None = kwargs.get("user") or kwargs.get("current_user")

            if not user:
                raise AuthorizationError(message="Authentication required")

            user_role = user.get("role", Role.GUEST)
            if not has_permission(user_role, permission):
                raise AuthorizationError(
                    message=f"Permission '{permission.value}' required",
                    details={"required": permission.value, "user_role": user_role},
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator