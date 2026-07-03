"""Conversation repository with domain-specific query methods."""

import uuid
from typing import Any, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.conversation import Conversation
from app.repositories.base import BaseRepository


class ConversationRepository(BaseRepository[Conversation]):
    """Repository for Conversation model operations.

    Extends BaseRepository with conversation-specific queries such as
    listing by user, loading with messages, and message count management.
    """

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(Conversation, db)

    async def get_by_user(
        self, user_id: uuid.UUID, skip: int = 0, limit: int = 20
    ) -> tuple[Sequence[Conversation], int]:
        """Retrieve a paginated list of conversations belonging to a user.

        Args:
            user_id: The UUID of the owning user.
            skip: Number of records to skip for pagination.
            limit: Maximum number of records to return.

        Returns:
            A tuple of (list of conversations, total count).
        """
        return await self.get_all(
            skip=skip,
            limit=limit,
            filters={"user_id": user_id},
            order_by="created_at",
            order_desc=True,
        )

    async def get_with_messages(
        self, conversation_id: uuid.UUID
    ) -> Conversation | None:
        """Retrieve a conversation eagerly loaded with its messages.

        Uses selectinload to eagerly load the messages relationship,
        avoiding N+1 queries when accessing conversation.messages.

        Args:
            conversation_id: The UUID of the conversation.

        Returns:
            The Conversation instance with messages loaded, or None if not found.
        """
        query = (
            select(Conversation)
            .where(
                Conversation.id == conversation_id,
                Conversation.is_deleted == False,
            )
            .options(selectinload(Conversation.messages))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def increment_message_count(
        self, conversation_id: uuid.UUID
    ) -> None:
        """Increment the message_count for a conversation by one.

        This is typically called after a new message is added to the
        conversation.

        Args:
            conversation_id: The UUID of the conversation to update.

        Raises:
            ValueError: If no conversation with the given ID is found.
        """
        conversation = await self.get_by_id(conversation_id)
        if conversation is None:
            raise ValueError(
                f"Conversation with id {conversation_id} not found"
            )
        conversation.message_count = (conversation.message_count or 0) + 1
        await self.db.flush()
