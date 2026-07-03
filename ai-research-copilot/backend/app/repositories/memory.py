"""Memory entry and user preference repository implementations."""

import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import ConversationBookmark, MemoryEntry, UserPreference
from app.repositories.base import BaseRepository


class MemoryEntryRepository(BaseRepository[MemoryEntry]):
    """Repository for MemoryEntry model operations.

    Provides user-scoped queries with optional memory_type filtering
    and pagination.
    """

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(MemoryEntry, db)

    async def get_by_user(
        self,
        user_id: uuid.UUID,
        memory_type: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[Sequence[MemoryEntry], int]:
        """Retrieve paginated memory entries for a user.

        Args:
            user_id: The UUID of the owning user.
            memory_type: Optional filter by memory type.
            skip: Number of records to skip for pagination.
            limit: Maximum number of records to return.

        Returns:
            A tuple of (list of memory entries, total count).
        """
        filters: dict[str, object] = {"user_id": user_id}
        if memory_type is not None:
            filters["memory_type"] = memory_type
        return await self.get_all(
            skip=skip,
            limit=limit,
            filters=filters,
            order_by="created_at",
            order_desc=True,
        )

    async def search_by_content(
        self,
        user_id: uuid.UUID,
        query: str,
        limit: int = 10,
    ) -> Sequence[MemoryEntry]:
        """Perform a simple ILIKE content search across active memory entries.

        This is a placeholder for a future vector-similarity search.
        For now it uses a case-insensitive LIKE match on the content column.

        Args:
            user_id: The UUID of the owning user.
            query: The search string to match against content.
            limit: Maximum number of results to return.

        Returns:
            A list of matching memory entries ordered by relevance score
            (descending) and then by creation time (descending).
        """
        search_pattern = f"%{query}%"
        stmt = (
            select(MemoryEntry)
            .where(
                MemoryEntry.user_id == user_id,
                MemoryEntry.is_deleted == False,  # noqa: E712
                MemoryEntry.is_active == True,  # noqa: E712
                MemoryEntry.content.ilike(search_pattern),
            )
            .order_by(
                MemoryEntry.relevance_score.desc().nullslast(),
                MemoryEntry.created_at.desc(),
            )
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()


class UserPreferenceRepository(BaseRepository[UserPreference]):
    """Repository for UserPreference model operations.

    Provides user-scoped queries and upsert logic for preference key-value pairs.
    """

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(UserPreference, db)

    async def get_by_user(
        self,
        user_id: uuid.UUID,
        category: str | None = None,
    ) -> Sequence[UserPreference]:
        """Retrieve all preferences for a user, optionally filtered by category.

        Args:
            user_id: The UUID of the owning user.
            category: Optional category to filter by.

        Returns:
            A list of matching user preferences.
        """
        filters: dict[str, object] = {"user_id": user_id}
        if category is not None:
            filters["category"] = category
        records, _ = await self.get_all(
            skip=0,
            limit=1000,
            filters=filters,
            order_by="category",
            order_desc=False,
        )
        return records

    async def get_by_user_category_key(
        self,
        user_id: uuid.UUID,
        category: str,
        key: str,
    ) -> UserPreference | None:
        """Retrieve a single preference by user, category, and key.

        Args:
            user_id: The UUID of the owning user.
            category: The preference category.
            key: The preference key within the category.

        Returns:
            The UserPreference instance if found, None otherwise.
        """
        stmt = (
            select(UserPreference)
            .where(
                UserPreference.user_id == user_id,
                UserPreference.category == category,
                UserPreference.key == key,
                UserPreference.is_deleted == False,  # noqa: E712
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert(
        self,
        user_id: uuid.UUID,
        category: str,
        key: str,
        value: dict,
    ) -> UserPreference:
        """Insert or update a preference value for the given user/category/key.

        If a preference with the same user_id, category, and key already exists
        (and is not soft-deleted), its value is updated. Otherwise a new record
        is created.

        Args:
            user_id: The UUID of the owning user.
            category: The preference category.
            key: The preference key within the category.
            value: The JSONB value to store.

        Returns:
            The created or updated UserPreference instance.
        """
        existing = await self.get_by_user_category_key(user_id, category, key)
        if existing is not None:
            existing.value = value
            await self.db.flush()
            await self.db.refresh(existing)
            return existing
        return await self.create(
            user_id=user_id,
            category=category,
            key=key,
            value=value,
        )


class ConversationBookmarkRepository(BaseRepository[ConversationBookmark]):
    """Repository for ConversationBookmark model operations.

    Provides user-scoped bookmark queries.
    """

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(ConversationBookmark, db)

    async def get_by_user(
        self,
        user_id: uuid.UUID,
    ) -> Sequence[ConversationBookmark]:
        """Retrieve all bookmarks for a user.

        Args:
            user_id: The UUID of the owning user.

        Returns:
            A list of bookmarks ordered by creation time (newest first).
        """
        records, _ = await self.get_all(
            skip=0,
            limit=1000,
            filters={"user_id": user_id},
            order_by="created_at",
            order_desc=True,
        )
        return records

    async def get_by_user_and_conversation(
        self,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
    ) -> ConversationBookmark | None:
        """Check whether a bookmark already exists for a user/conversation pair.

        Args:
            user_id: The UUID of the owning user.
            conversation_id: The UUID of the conversation.

        Returns:
            The ConversationBookmark instance if found, None otherwise.
        """
        stmt = (
            select(ConversationBookmark)
            .where(
                ConversationBookmark.user_id == user_id,
                ConversationBookmark.conversation_id == conversation_id,
                ConversationBookmark.is_deleted == False,  # noqa: E712
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
