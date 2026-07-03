"""Message repository with domain-specific query methods."""

import uuid
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.conversation import Message
from app.repositories.base import BaseRepository


class MessageRepository(BaseRepository[Message]):
    """Repository for Message model operations.

    Extends BaseRepository with message-specific queries such as
    listing messages by conversation with parent loading.
    """

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Message, db)

    async def get_by_conversation(
        self,
        conversation_id: uuid.UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[Sequence[Message], int]:
        """Retrieve a paginated list of messages in a conversation.

        Messages are ordered by creation time ascending (oldest first)
        to maintain chronological order. Eagerly loads parent_message
        to avoid N+1 queries.

        Args:
            conversation_id: The UUID of the parent conversation.
            skip: Number of records to skip for pagination.
            limit: Maximum number of records to return.

        Returns:
            A tuple of (list of messages, total count).
        """
        query = (
            select(Message)
            .where(
                Message.conversation_id == conversation_id,
                Message.is_deleted == False,
            )
            .options(selectinload(Message.parent_message))
        )

        count_query = (
            select(func.count())
            .select_from(Message)
            .where(
                Message.conversation_id == conversation_id,
                Message.is_deleted == False,
            )
        )

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(Message.created_at.asc())
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all(), total
