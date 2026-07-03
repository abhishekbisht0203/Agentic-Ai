"""User management service for profile, API keys, and audit logs."""

import hashlib
import secrets
import uuid
from datetime import datetime, timezone

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.models.user import APIKey, AuditLog, User
from app.repositories.user import UserRepository
from app.schemas.user import (
    APIKeyCreate,
    APIKeyCreated,
    APIKeyResponse,
    AuditLogResponse,
    UserList,
    UserPreferencesUpdate,
    UserResponse,
    UserUpdate,
)


class UserService:
    """Service for user management operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.user_repo = UserRepository(db)

    async def get_user(self, user_id: uuid.UUID) -> User:
        """Retrieve a user by ID.

        Args:
            user_id: UUID of the user to retrieve.

        Returns:
            The User model instance.

        Raises:
            NotFoundError: If no user with the given ID exists.
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError(message=f"User with id {user_id} not found")
        return user

    async def list_users(
        self, page: int = 1, page_size: int = 20, search: str | None = None
    ) -> UserList:
        """List users with pagination and optional search.

        Search matches against email, username, and full_name using
        case-insensitive contains.

        Args:
            page: Page number (1-indexed).
            page_size: Number of items per page.
            search: Optional search string to filter users.

        Returns:
            UserList containing paginated user records and total count.
        """
        skip = (page - 1) * page_size

        query = select(User).where(User.is_deleted == False)
        count_query = (
            select(func.count())
            .select_from(User)
            .where(User.is_deleted == False)
        )

        if search:
            search_pattern = f"%{search}%"
            search_filter = (
                User.email.ilike(search_pattern)
                | User.username.ilike(search_pattern)
                | User.full_name.ilike(search_pattern)
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)

        query = query.order_by(desc(User.created_at)).offset(skip).limit(page_size)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        result = await self.db.execute(query)
        users = result.scalars().all()

        return UserList(
            items=[UserResponse.model_validate(u) for u in users],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def update_user(self, user_id: uuid.UUID, data: UserUpdate) -> User:
        """Update user profile fields.

        Validates uniqueness constraints for email and username before
        applying changes.

        Args:
            user_id: UUID of the user to update.
            data: User update schema with fields to change.

        Returns:
            The updated User instance.

        Raises:
            NotFoundError: If user not found.
            ValidationError: If email or username conflicts with another user.
        """
        user = await self.get_user(user_id)

        update_data = data.model_dump(exclude_unset=True)

        if "email" in update_data and update_data["email"] != user.email:
            existing = await self.user_repo.get_by_email(update_data["email"])
            if existing:
                raise ValidationError(message="Email already in use")

        if "username" in update_data and update_data["username"] != user.username:
            existing = await self.user_repo.get_by_username(update_data["username"])
            if existing:
                raise ValidationError(message="Username already taken")

        updated = await self.user_repo.update(user_id, **update_data)
        if not updated:
            raise NotFoundError(message=f"User with id {user_id} not found")
        return updated

    async def delete_user(self, user_id: uuid.UUID) -> None:
        """Soft-delete a user and all associated data.

        Args:
            user_id: UUID of the user to delete.

        Raises:
            NotFoundError: If user not found.
        """
        deleted = await self.user_repo.delete(user_id, soft=True)
        if not deleted:
            raise NotFoundError(message=f"User with id {user_id} not found")

    async def update_preferences(
        self, user_id: uuid.UUID, preferences: UserPreferencesUpdate
    ) -> dict:
        """Replace user preferences with new values.

        Args:
            user_id: UUID of the user whose preferences to update.
            preferences: Preferences schema containing the new preference dict.

        Returns:
            The updated preferences dictionary.

        Raises:
            NotFoundError: If user not found.
        """
        user = await self.get_user(user_id)
        updated = await self.user_repo.update(user_id, preferences=preferences.preferences)
        if not updated:
            raise NotFoundError(message=f"User with id {user_id} not found")
        return updated.preferences or {}

    async def create_api_key(
        self, user_id: uuid.UUID, data: APIKeyCreate
    ) -> APIKeyCreated:
        """Create a new API key for a user.

        Generates a cryptographically secure key, hashes it for storage,
        and returns the full key only at creation time.

        Args:
            user_id: UUID of the user owning the key.
            data: API key creation schema with name and optional scopes.

        Returns:
            APIKeyCreated with full key value (only shown once).

        Raises:
            NotFoundError: If user not found.
        """
        await self.get_user(user_id)

        raw_key = secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        key_prefix = raw_key[:8]

        api_key = APIKey(
            user_id=user_id,
            name=data.name,
            key_hash=key_hash,
            key_prefix=key_prefix,
            scopes=data.scopes or [],
            expires_at=data.expires_at,
        )
        self.db.add(api_key)
        await self.db.flush()
        await self.db.refresh(api_key)

        return APIKeyCreated(
            id=api_key.id,
            name=api_key.name,
            key_prefix=api_key.key_prefix,
            scopes=api_key.scopes,
            is_active=api_key.is_active,
            expires_at=api_key.expires_at,
            last_used_at=api_key.last_used_at,
            created_at=api_key.created_at,
            full_key=raw_key,
        )

    async def list_api_keys(self, user_id: uuid.UUID) -> list[APIKeyResponse]:
        """List all API keys for a user.

        Does NOT include the full key value for security.

        Args:
            user_id: UUID of the user whose keys to list.

        Returns:
            List of APIKeyResponse schemas.
        """
        query = (
            select(APIKey)
            .where(APIKey.user_id == user_id, APIKey.is_deleted == False)
            .order_by(desc(APIKey.created_at))
        )
        result = await self.db.execute(query)
        keys = result.scalars().all()

        return [
            APIKeyResponse(
                id=k.id,
                name=k.name,
                key_prefix=k.key_prefix,
                scopes=k.scopes,
                is_active=k.is_active,
                expires_at=k.expires_at,
                last_used_at=k.last_used_at,
                created_at=k.created_at,
            )
            for k in keys
        ]

    async def revoke_api_key(self, user_id: uuid.UUID, key_id: uuid.UUID) -> None:
        """Revoke (soft-delete) an API key.

        Args:
            user_id: UUID of the user who owns the key.
            key_id: UUID of the API key to revoke.

        Raises:
            NotFoundError: If the API key is not found or does not belong to the user.
        """
        query = select(APIKey).where(
            APIKey.id == key_id,
            APIKey.user_id == user_id,
            APIKey.is_deleted == False,
        )
        result = await self.db.execute(query)
        api_key = result.scalar_one_or_none()

        if not api_key:
            raise NotFoundError(message=f"API key with id {key_id} not found")

        api_key.is_active = False
        api_key.is_deleted = True
        api_key.deleted_at = datetime.now(timezone.utc)
        await self.db.flush()

    async def get_audit_logs(
        self, user_id: uuid.UUID, page: int = 1, page_size: int = 20
    ) -> list[AuditLogResponse]:
        """Retrieve paginated audit logs for a user.

        Args:
            user_id: UUID of the user whose audit logs to retrieve.
            page: Page number (1-indexed).
            page_size: Number of items per page.

        Returns:
            List of AuditLogResponse schemas for the requested page.
        """
        skip = (page - 1) * page_size

        query = (
            select(AuditLog)
            .where(AuditLog.user_id == user_id)
            .order_by(desc(AuditLog.created_at))
            .offset(skip)
            .limit(page_size)
        )
        result = await self.db.execute(query)
        logs = result.scalars().all()

        return [
            AuditLogResponse(
                id=log.id,
                user_id=log.user_id,
                action=log.action,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                details=log.details,
                status=log.status,
                created_at=log.created_at,
            )
            for log in logs
        ]
