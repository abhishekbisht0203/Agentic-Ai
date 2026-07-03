"""Knowledge base repository with domain-specific query methods."""

import uuid
from typing import Any, Sequence

from sqlalchemy import delete, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import KnowledgeBase, KnowledgeBaseDocument
from app.repositories.base import BaseRepository


class KnowledgeBaseRepository(BaseRepository[KnowledgeBase]):
    """Repository for KnowledgeBase model operations.

    Extends BaseRepository with knowledge base-specific queries such as
    listing by user and managing document associations.
    """

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(KnowledgeBase, db)

    async def get_by_user(
        self, user_id: uuid.UUID, skip: int = 0, limit: int = 20
    ) -> tuple[Sequence[KnowledgeBase], int]:
        """Retrieve a paginated list of knowledge bases belonging to a user.

        Args:
            user_id: The UUID of the owning user.
            skip: Number of records to skip for pagination.
            limit: Maximum number of records to return.

        Returns:
            A tuple of (list of knowledge bases, total count).
        """
        return await self.get_all(
            skip=skip,
            limit=limit,
            filters={"user_id": user_id},
            order_by="created_at",
            order_desc=True,
        )

    async def add_documents(
        self, kb_id: uuid.UUID, doc_ids: list[uuid.UUID]
    ) -> None:
        """Associate documents with a knowledge base.

        Inserts rows into the junction table linking the knowledge base
        to the specified documents. Skips duplicate associations.

        Args:
            kb_id: The UUID of the knowledge base.
            doc_ids: A list of document UUIDs to associate.

        Raises:
            ValueError: If no document IDs are provided.
        """
        if not doc_ids:
            raise ValueError("At least one document ID must be provided")

        rows = [
            {"knowledge_base_id": kb_id, "document_id": doc_id}
            for doc_id in doc_ids
        ]
        stmt = insert(KnowledgeBaseDocument).values(rows)
        stmt = stmt.on_conflict_do_nothing(
            constraint="knowledge_base_documents_pkey"
        )
        await self.db.execute(stmt)

        # Update document_count on the knowledge base
        kb = await self.get_by_id(kb_id)
        if kb is not None:
            count_stmt = (
                select(KnowledgeBaseDocument)
                .where(KnowledgeBaseDocument.knowledge_base_id == kb_id)
            )
            result = await self.db.execute(count_stmt)
            kb.document_count = len(result.all())
            await self.db.flush()

    async def remove_documents(
        self, kb_id: uuid.UUID, doc_ids: list[uuid.UUID]
    ) -> None:
        """Remove document associations from a knowledge base.

        Deletes rows from the junction table for the specified documents.

        Args:
            kb_id: The UUID of the knowledge base.
            doc_ids: A list of document UUIDs to disassociate.

        Raises:
            ValueError: If no document IDs are provided.
        """
        if not doc_ids:
            raise ValueError("At least one document ID must be provided")

        stmt = (
            delete(KnowledgeBaseDocument)
            .where(
                KnowledgeBaseDocument.knowledge_base_id == kb_id,
                KnowledgeBaseDocument.document_id.in_(doc_ids),
            )
        )
        await self.db.execute(stmt)

        # Update document_count on the knowledge base
        kb = await self.get_by_id(kb_id)
        if kb is not None:
            count_stmt = (
                select(KnowledgeBaseDocument)
                .where(KnowledgeBaseDocument.knowledge_base_id == kb_id)
            )
            result = await self.db.execute(count_stmt)
            kb.document_count = len(result.all())
            await self.db.flush()
