"""Document repository with domain-specific query methods."""

import uuid
from typing import Any, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    """Repository for Document model operations.

    Extends BaseRepository with document-specific queries such as
    listing documents by user and retrieving processing-ready documents.
    """

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Document, db)

    async def get_by_user(
        self, user_id: uuid.UUID, skip: int = 0, limit: int = 20
    ) -> tuple[Sequence[Document], int]:
        """Retrieve a paginated list of documents belonging to a user.

        Args:
            user_id: The UUID of the owning user.
            skip: Number of records to skip for pagination.
            limit: Maximum number of records to return.

        Returns:
            A tuple of (list of documents, total count).
        """
        return await self.get_all(
            skip=skip,
            limit=limit,
            filters={"user_id": user_id},
            order_by="created_at",
            order_desc=True,
        )

    async def get_ready_documents(
        self, user_id: uuid.UUID
    ) -> list[Document]:
        """Retrieve all documents for a user that have completed processing.

        Returns documents with status 'ready' that can be used in
        knowledge bases and RAG operations.

        Args:
            user_id: The UUID of the owning user.

        Returns:
            A list of Document instances with status 'ready'.
        """
        query = select(Document).where(
            Document.user_id == user_id,
            Document.status == "ready",
            Document.is_deleted == False,
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
