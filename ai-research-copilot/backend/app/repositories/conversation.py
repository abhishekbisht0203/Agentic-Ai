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

    async def get_by_user_light(
        self, user_id: uuid.UUID, skip: int = 0, limit: int = 20
    ) -> tuple[Sequence[Conversation], int]:
        """Retrieve a lightweight paginated list for sidebar display.

        Only selects columns needed for the conversation list UI,
        avoiding loading heavy fields like description and knowledge_base_id.

        Args:
            user_id: The UUID of the owning user.
            skip: Number of records to skip for pagination.
            limit: Maximum number of records to return.

        Returns:
            A tuple of (list of conversations, total count).
        """
        from sqlalchemy import func

        # Lightweight query - only essential columns
        query = (
            select(Conversation.id, Conversation.title, Conversation.created_at,
                   Conversation.updated_at, Conversation.message_count,
                   Conversation.agent_type)
            .where(
                Conversation.user_id == user_id,
                Conversation.is_deleted == False,
            )
            .order_by(Conversation.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        count_query = (
            select(func.count())
            .select_from(Conversation)
            .where(
                Conversation.user_id == user_id,
                Conversation.is_deleted == False,
            )
        )

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        result = await self.db.execute(query)
        rows = result.all()

        # Convert rows to Conversation-like objects for compatibility
        conversations = []
        for row in rows:
            conv = Conversation(
                id=row.id,
                title=row.title,
                created_at=row.created_at,
                updated_at=row.updated_at,
                message_count=row.message_count,
                agent_type=row.agent_type,
            )
            conversations.append(conv)

        return conversations, total

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
