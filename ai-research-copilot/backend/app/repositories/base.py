"""Base repository with common CRUD operations."""

import uuid
from datetime import datetime, timezone
from typing import Any, Generic, Sequence, TypeVar

from sqlalchemy import Select, select, func, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseRepository(Generic[ModelType]):
    """Base repository providing common CRUD operations for SQLAlchemy models.

    Provides generic methods for get, create, update, delete, and list
    operations with filtering, sorting, and pagination support.

    Attributes:
        model: The SQLAlchemy model class this repository manages.
        db: The async database session used for queries.
    """

    def __init__(self, model: type[ModelType], db: AsyncSession) -> None:
        self.model = model
        self.db = db

    async def get_by_id(self, id: uuid.UUID) -> ModelType | None:
        """Retrieve a single record by its primary key.

        Args:
            id: The UUID primary key of the record.

        Returns:
            The model instance if found, None otherwise.
        """
        return await self.db.get(self.model, id)

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 20,
        filters: dict[str, Any] | None = None,
        order_by: str | None = None,
        order_desc: bool = True,
    ) -> tuple[Sequence[ModelType], int]:
        """Retrieve a paginated list of non-deleted records.

        Args:
            skip: Number of records to skip for pagination.
            limit: Maximum number of records to return.
            filters: Optional dictionary of column name to value filters.
            order_by: Optional column name to sort by.
            order_desc: Whether to sort in descending order.

        Returns:
            A tuple of (list of records, total count matching filters).
        """
        query = select(self.model).where(self.model.is_deleted == False)
        count_query = (
            select(func.count())
            .select_from(self.model)
            .where(self.model.is_deleted == False)
        )

        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key) and value is not None:
                    query = query.where(getattr(self.model, key) == value)
                    count_query = count_query.where(
                        getattr(self.model, key) == value
                    )

        if order_by and hasattr(self.model, order_by):
            col = getattr(self.model, order_by)
            query = query.order_by(desc(col) if order_desc else asc(col))

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all(), total

    async def create(self, **kwargs: Any) -> ModelType:
        """Create a new record.

        Args:
            **kwargs: Column name-value pairs for the new record.

        Returns:
            The created model instance with generated fields populated.
        """
        instance = self.model(**kwargs)
        self.db.add(instance)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def update(self, id: uuid.UUID, **kwargs: Any) -> ModelType | None:
        """Update an existing record by ID.

        Only updates columns that are present in kwargs and exist on the model.
        The updated_at timestamp is automatically set by the database.

        Args:
            id: The UUID primary key of the record to update.
            **kwargs: Column name-value pairs to update.

        Returns:
            The updated model instance, or None if not found.
        """
        instance = await self.get_by_id(id)
        if instance:
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            await self.db.flush()
            await self.db.refresh(instance)
        return instance

    async def delete(self, id: uuid.UUID, soft: bool = True) -> bool:
        """Delete a record by ID.

        Args:
            id: The UUID primary key of the record to delete.
            soft: If True, marks the record as deleted (soft delete).
                  If False, permanently removes the record (hard delete).

        Returns:
            True if the record was found and deleted, False otherwise.
        """
        instance = await self.get_by_id(id)
        if instance:
            if soft:
                instance.is_deleted = True
                instance.deleted_at = datetime.now(timezone.utc)
            else:
                await self.db.delete(instance)
            await self.db.flush()
            return True
        return False

    async def count(self, filters: dict[str, Any] | None = None) -> int:
        """Count non-deleted records, optionally filtered.

        Args:
            filters: Optional dictionary of column name to value filters.

        Returns:
            The count of matching records.
        """
        query = (
            select(func.count())
            .select_from(self.model)
            .where(self.model.is_deleted == False)
        )
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key) and value is not None:
                    query = query.where(getattr(self.model, key) == value)
        result = await self.db.execute(query)
        return result.scalar() or 0
