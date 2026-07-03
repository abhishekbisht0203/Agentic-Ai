"""Memory and user-preference service layer.

Handles all business logic for long-term memory entries, semantic search,
and user preference management including ownership validation, pagination,
and error handling.
"""

import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.exceptions import (
    AuthorizationError,
    DatabaseError,
    NotFoundError,
    ValidationError,
)
from app.repositories.memory import MemoryEntryRepository, UserPreferenceRepository
from app.schemas.memory import (
    MemoryEntryCreate,
    MemoryEntryList,
    MemoryEntryResponse,
    MemoryEntryUpdate,
    UserPreferenceResponse,
    UserPreferenceUpdate,
)


class MemoryService:
    """Service for managing long-term memory entries and user preferences.

    Coordinates between MemoryEntryRepository and UserPreferenceRepository
    to implement business workflows while keeping controllers thin.

    Args:
        db: An async database session.  The caller is responsible for
            managing the session lifecycle (begin / commit / rollback).
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._memory_repo = MemoryEntryRepository(db)
        self._pref_repo = UserPreferenceRepository(db)

    # ------------------------------------------------------------------
    # Memory entries
    # ------------------------------------------------------------------

    async def create_memory_entry(
        self,
        user_id: uuid.UUID,
        data: MemoryEntryCreate,
    ) -> MemoryEntryResponse:
        """Create a new memory entry for the given user.

        Args:
            user_id: The UUID of the user who owns the memory.
            data: Validated request payload.

        Returns:
            The newly created memory entry.

        Raises:
            DatabaseError: If the underlying database operation fails.
        """
        try:
            entry = await self._memory_repo.create(
                user_id=user_id,
                content=data.content,
                memory_type=data.memory_type,
                source=data.source,
                metadata_extra=data.metadata_extra,
            )
            await self._db.commit()
        except Exception as exc:
            await self._db.rollback()
            raise DatabaseError(
                message="Failed to create memory entry",
                details={"error": str(exc)},
            ) from exc

        return MemoryEntryResponse.model_validate(entry)

    async def list_memory_entries(
        self,
        user_id: uuid.UUID,
        memory_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> MemoryEntryList:
        """List memory entries for a user with optional type filter.

        Args:
            user_id: The UUID of the owning user.
            memory_type: Optional filter by memory type.
            page: 1-indexed page number.
            page_size: Number of items per page (1-100).

        Returns:
            A paginated list of memory entries.
        """
        skip = (page - 1) * page_size
        items, total = await self._memory_repo.get_by_user(
            user_id=user_id,
            memory_type=memory_type,
            skip=skip,
            limit=page_size,
        )

        return MemoryEntryList(
            items=[MemoryEntryResponse.model_validate(e) for e in items],
            total=total,
        )

    async def update_memory_entry(
        self,
        entry_id: uuid.UUID,
        user_id: uuid.UUID,
        data: MemoryEntryUpdate,
    ) -> MemoryEntryResponse:
        """Update a memory entry with ownership check.

        Only the fields explicitly set in the request body are updated.

        Args:
            entry_id: The UUID of the memory entry to update.
            user_id: The UUID of the requesting user.
            data: Validated update payload.

        Returns:
            The updated memory entry.

        Raises:
            NotFoundError: If no memory entry with the given ID exists.
            AuthorizationError: If the user does not own the entry.
            DatabaseError: If the underlying database operation fails.
        """
        entry = await self._memory_repo.get_by_id(entry_id)
        if entry is None or entry.is_deleted:
            raise NotFoundError(
                message="Memory entry not found",
                details={"entry_id": str(entry_id)},
            )
        if entry.user_id != user_id:
            raise AuthorizationError(
                message="You do not have access to this memory entry",
                details={"entry_id": str(entry_id)},
            )

        update_fields = data.model_dump(exclude_unset=True)
        if not update_fields:
            return MemoryEntryResponse.model_validate(entry)

        try:
            updated = await self._memory_repo.update(entry_id, **update_fields)
            await self._db.commit()
        except Exception as exc:
            await self._db.rollback()
            raise DatabaseError(
                message="Failed to update memory entry",
                details={"error": str(exc)},
            ) from exc

        return MemoryEntryResponse.model_validate(updated)

    async def delete_memory_entry(
        self,
        entry_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        """Soft-delete a memory entry with ownership check.

        Args:
            entry_id: The UUID of the memory entry to delete.
            user_id: The UUID of the requesting user.

        Raises:
            NotFoundError: If no memory entry with the given ID exists.
            AuthorizationError: If the user does not own the entry.
            DatabaseError: If the underlying database operation fails.
        """
        entry = await self._memory_repo.get_by_id(entry_id)
        if entry is None or entry.is_deleted:
            raise NotFoundError(
                message="Memory entry not found",
                details={"entry_id": str(entry_id)},
            )
        if entry.user_id != user_id:
            raise AuthorizationError(
                message="You do not have access to this memory entry",
                details={"entry_id": str(entry_id)},
            )

        try:
            await self._memory_repo.delete(entry_id, soft=True)
            await self._db.commit()
        except Exception as exc:
            await self._db.rollback()
            raise DatabaseError(
                message="Failed to delete memory entry",
                details={"error": str(exc)},
            ) from exc

    async def search_memory(
        self,
        user_id: uuid.UUID,
        query: str,
        limit: int = 10,
    ) -> list[MemoryEntryResponse]:
        """Search memory entries by content using semantic similarity.

        This method currently performs an ILIKE content search as a
        placeholder.  When a vector store is available, this should be
        replaced with an embedding-based cosine-similarity search.

        Args:
            user_id: The UUID of the user whose memories to search.
            query: The search string.
            limit: Maximum number of results (default 10).

        Returns:
            A list of matching memory entries ordered by relevance.
        """
        if not query or not query.strip():
            raise ValidationError(
                message="Search query must not be empty",
            )

        entries = await self._memory_repo.search_by_content(
            user_id=user_id,
            query=query.strip(),
            limit=limit,
        )
        return [MemoryEntryResponse.model_validate(e) for e in entries]

    # ------------------------------------------------------------------
    # User preferences
    # ------------------------------------------------------------------

    async def get_preferences(
        self,
        user_id: uuid.UUID,
    ) -> list[UserPreferenceResponse]:
        """Retrieve all preferences for a user.

        Args:
            user_id: The UUID of the owning user.

        Returns:
            A list of user preferences.
        """
        preferences = await self._pref_repo.get_by_user(user_id=user_id)
        return [
            UserPreferenceResponse.model_validate(p) for p in preferences
        ]

    async def update_preference(
        self,
        user_id: uuid.UUID,
        data: UserPreferenceUpdate,
    ) -> UserPreferenceResponse:
        """Create or update a user preference.

        If a preference with the same category and key already exists for
        the user its value is replaced; otherwise a new preference is created.

        Args:
            user_id: The UUID of the owning user.
            data: Validated preference payload.

        Returns:
            The created or updated user preference.

        Raises:
            DatabaseError: If the underlying database operation fails.
        """
        try:
            preference = await self._pref_repo.upsert(
                user_id=user_id,
                category=data.category,
                key=data.key,
                value=data.value,
            )
            await self._db.commit()
        except Exception as exc:
            await self._db.rollback()
            raise DatabaseError(
                message="Failed to update preference",
                details={
                    "category": data.category,
                    "key": data.key,
                    "error": str(exc),
                },
            ) from exc

        return UserPreferenceResponse.model_validate(preference)
