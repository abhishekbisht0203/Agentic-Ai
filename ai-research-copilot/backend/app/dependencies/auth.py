"""Authentication dependencies for FastAPI dependency injection."""

import uuid
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.security.auth import verify_token
from app.core.security.permissions import Permission, Role, has_permission
from app.database.session import get_db_session
from app.models.user import User

security = HTTPBearer()


async def get_current_user_from_token(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> User:
    """Get current authenticated user from JWT token."""
    token = credentials.credentials
    payload = verify_token(token)
    try:
        user_id = uuid.UUID(payload.sub)
    except ValueError:
        raise AuthenticationError(message="Invalid token subject")
    user = await db.get(User, user_id)
    if not user or not user.is_active:
        raise AuthenticationError(message="User not found or inactive")
    return user


def require_role(role: Role):
    """Dependency factory that requires a specific role."""

    async def _check_role(
        current_user: Annotated[User, Depends(get_current_user_from_token)],
    ) -> User:
        user_role = Role(current_user.role.value)
        if not has_permission(user_role, Permission.ALL) and user_role != role:
            raise AuthorizationError(
                message=f"Role '{role.value}' required",
                details={"required": role.value, "current": user_role.value},
            )
        return current_user

    return _check_role


def require_permission(permission: Permission):
    """Dependency factory that requires a specific permission."""

    async def _check_perm(
        current_user: Annotated[User, Depends(get_current_user_from_token)],
    ) -> User:
        user_role = Role(current_user.role.value)
        if not has_permission(user_role, permission):
            raise AuthorizationError(
                message=f"Permission '{permission.value}' required",
                details={"required": permission.value, "user_role": user_role.value},
            )
        return current_user

    return _check_perm
