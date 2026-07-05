"""User repository with domain-specific query methods."""

import uuid
from datetime import datetime, timezone
from typing import Any, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User model operations.

    Extends BaseRepository with user-specific queries such as
    lookup by email, username, and OAuth credentials.
    """

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> User | None:
        """Retrieve a user by email address.

        Args:
            email: The email address to search for.

        Returns:
            The matching User instance, or None if not found.
        """
        query = select(User).where(
            User.email == email,
            User.is_deleted == False,
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        """Retrieve a user by username.

        Args:
            username: The username to search for.

        Returns:
            The matching User instance, or None if not found.
        """
        query = select(User).where(
            User.username == username,
            User.is_deleted == False,
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_oauth(
        self, oauth_provider: str, oauth_id: str
    ) -> User | None:
        """Retrieve a user by OAuth provider and external user ID.

        Supports lookup by dedicated provider columns (google_id, github_id)
        as well as the legacy oauth_provider/oauth_id columns.

        Args:
            oauth_provider: The OAuth provider name (e.g., 'github', 'google').
            oauth_id: The external user ID from the OAuth provider.

        Returns:
            The matching User instance, or None if not found.
        """
        # Check dedicated columns first
        if oauth_provider == "google":
            query = select(User).where(
                User.google_id == oauth_id,
                User.is_deleted == False,
            )
        elif oauth_provider == "github":
            query = select(User).where(
                User.github_id == oauth_id,
                User.is_deleted == False,
            )
        else:
            # Fallback to legacy columns
            query = select(User).where(
                User.oauth_provider == oauth_provider,
                User.oauth_id == oauth_id,
                User.is_deleted == False,
            )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_google_id(self, google_id: str) -> User | None:
        """Retrieve a user by Google ID.

        Args:
            google_id: The Google OAuth user ID.

        Returns:
            The matching User instance, or None if not found.
        """
        query = select(User).where(
            User.google_id == google_id,
            User.is_deleted == False,
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_github_id(self, github_id: str) -> User | None:
        """Retrieve a user by GitHub ID.

        Args:
            github_id: The GitHub OAuth user ID.

        Returns:
            The matching User instance, or None if not found.
        """
        query = select(User).where(
            User.github_id == github_id,
            User.is_deleted == False,
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_user(self, **kwargs: Any) -> User:
        """Create a new user with the provided attributes.

        Convenience method that delegates to the base create method.
        Validates that required fields (email, username) are present
        via the model constraints.

        Args:
            **kwargs: Column name-value pairs for the new user.

        Returns:
            The created User instance.

        Raises:
            sqlalchemy.exc.IntegrityError: If email or username already exists.
        """
        return await self.create(**kwargs)

    async def update_last_login(self, user_id: uuid.UUID) -> None:
        """Update the last_login_at timestamp for a user.

        Sets the timestamp to the current UTC time. This is typically
        called after successful authentication.

        Args:
            user_id: The UUID of the user to update.

        Raises:
            ValueError: If no user with the given ID is found.
        """
        user = await self.get_by_id(user_id)
        if user is None:
            raise ValueError(f"User with id {user_id} not found")
        user.last_login_at = datetime.now(timezone.utc)
        await self.db.flush()
