"""Chat and conversation service layer.

Handles all business logic for conversations, messages, and bookmarks
including ownership validation, pagination, and error handling.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.exceptions import (
    AuthorizationError,
    DatabaseError,
    NotFoundError,
    ValidationError,
)

from app.repositories.conversation import ConversationRepository
from app.repositories.memory import ConversationBookmarkRepository
from app.repositories.message import MessageRepository
from app.schemas.chat import (
    ConversationBookmarkCreate,
    ConversationBookmarkResponse,
    ConversationCreate,
    ConversationDetail,
    ConversationList,
    ConversationResponse,
    ConversationUpdate,
    MessageCreate,
    MessageList,
    MessageResponse,
)


class ChatService:
    """Service for managing chat conversations, messages, and bookmarks.

    Coordinates between ConversationRepository, MessageRepository, and
    ConversationBookmarkRepository to implement business workflows while
    keeping controllers thin.

    Args:
        db: An async database session.  The caller is responsible for
            managing the session lifecycle (begin / commit / rollback).
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._conv_repo = ConversationRepository(db)
        self._msg_repo = MessageRepository(db)
        self._bookmark_repo = ConversationBookmarkRepository(db)

    # ------------------------------------------------------------------
    # Conversation CRUD
    # ------------------------------------------------------------------

    async def create_conversation(
        self,
        user_id: uuid.UUID,
        data: ConversationCreate,
    ) -> ConversationResponse:
        """Create a new conversation for the given user.

        Args:
            user_id: The UUID of the user who owns the conversation.
            data: Validated request payload.

        Returns:
            The newly created conversation.

        Raises:
            DatabaseError: If the underlying database operation fails.
        """
        try:
            conversation = await self._conv_repo.create(
                user_id=user_id,
                title=data.title,
                description=data.description,
                agent_type=data.agent_type,
                knowledge_base_id=data.knowledge_base_id,
            )
            await self._db.commit()
        except Exception as exc:
            await self._db.rollback()
            raise DatabaseError(
                message="Failed to create conversation",
                details={"error": str(exc)},
            ) from exc

        return ConversationResponse.model_validate(conversation)

    async def get_conversation(
        self,
        conv_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> ConversationDetail:
        """Retrieve a single conversation by ID with ownership check.

        Args:
            conv_id: The UUID of the conversation.
            user_id: The UUID of the requesting user.

        Returns:
            The conversation detail.

        Raises:
            NotFoundError: If no conversation with the given ID exists.
            AuthorizationError: If the user does not own the conversation.
        """
        conversation = await self._conv_repo.get_by_id(conv_id)
        if conversation is None or conversation.is_deleted:
            raise NotFoundError(
                message="Conversation not found",
                details={"conversation_id": str(conv_id)},
            )
        if conversation.user_id != user_id:
            raise AuthorizationError(
                message="You do not have access to this conversation",
                details={"conversation_id": str(conv_id)},
            )

        return ConversationDetail.model_validate(conversation)

    async def list_conversations(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> ConversationList:
        """List all conversations for a user with pagination.

        Args:
            user_id: The UUID of the owning user.
            page: 1-indexed page number.
            page_size: Number of items per page (1-100).

        Returns:
            A paginated list of conversations.
        """
        skip = (page - 1) * page_size
        items, total = await self._conv_repo.get_by_user(
            user_id=user_id,
            skip=skip,
            limit=page_size,
        )

        return ConversationList(
            items=[ConversationResponse.model_validate(c) for c in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def update_conversation(
        self,
        conv_id: uuid.UUID,
        user_id: uuid.UUID,
        data: ConversationUpdate,
    ) -> ConversationResponse:
        """Update conversation metadata with ownership check.

        Only the fields explicitly set in the request body are updated.

        Args:
            conv_id: The UUID of the conversation to update.
            user_id: The UUID of the requesting user.
            data: Validated update payload.

        Returns:
            The updated conversation.

        Raises:
            NotFoundError: If no conversation with the given ID exists.
            AuthorizationError: If the user does not own the conversation.
            DatabaseError: If the underlying database operation fails.
        """
        conversation = await self._conv_repo.get_by_id(conv_id)
        if conversation is None or conversation.is_deleted:
            raise NotFoundError(
                message="Conversation not found",
                details={"conversation_id": str(conv_id)},
            )
        if conversation.user_id != user_id:
            raise AuthorizationError(
                message="You do not have access to this conversation",
                details={"conversation_id": str(conv_id)},
            )

        update_fields = data.model_dump(exclude_unset=True)
        if not update_fields:
            return ConversationResponse.model_validate(conversation)

        try:
            updated = await self._conv_repo.update(conv_id, **update_fields)
            await self._db.commit()
        except Exception as exc:
            await self._db.rollback()
            raise DatabaseError(
                message="Failed to update conversation",
                details={"error": str(exc)},
            ) from exc

        return ConversationResponse.model_validate(updated)

    async def delete_conversation(
        self,
        conv_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        """Soft-delete a conversation with ownership check.

        Args:
            conv_id: The UUID of the conversation to delete.
            user_id: The UUID of the requesting user.

        Raises:
            NotFoundError: If no conversation with the given ID exists.
            AuthorizationError: If the user does not own the conversation.
            DatabaseError: If the underlying database operation fails.
        """
        conversation = await self._conv_repo.get_by_id(conv_id)
        if conversation is None or conversation.is_deleted:
            raise NotFoundError(
                message="Conversation not found",
                details={"conversation_id": str(conv_id)},
            )
        if conversation.user_id != user_id:
            raise AuthorizationError(
                message="You do not have access to this conversation",
                details={"conversation_id": str(conv_id)},
            )

        try:
            await self._conv_repo.delete(conv_id, soft=True)
            await self._db.commit()
        except Exception as exc:
            await self._db.rollback()
            raise DatabaseError(
                message="Failed to delete conversation",
                details={"error": str(exc)},
            ) from exc

    # ------------------------------------------------------------------
    # Messages
    # ------------------------------------------------------------------

    async def add_message(
        self,
        conv_id: uuid.UUID,
        user_id: uuid.UUID,
        data: MessageCreate,
    ) -> MessageResponse:
        """Add a message to a conversation.

        Verifies that the conversation exists and is owned by the user
        before inserting the message.  The conversation's message_count
        is incremented atomically.

        Args:
            conv_id: The UUID of the target conversation.
            user_id: The UUID of the requesting user.
            data: Validated message payload.

        Returns:
            The newly created message.

        Raises:
            NotFoundError: If no conversation with the given ID exists.
            AuthorizationError: If the user does not own the conversation.
            DatabaseError: If the underlying database operation fails.
        """
        conversation = await self._conv_repo.get_by_id(conv_id)
        if conversation is None or conversation.is_deleted:
            raise NotFoundError(
                message="Conversation not found",
                details={"conversation_id": str(conv_id)},
            )
        if conversation.user_id != user_id:
            raise AuthorizationError(
                message="You do not have access to this conversation",
                details={"conversation_id": str(conv_id)},
            )

        try:
            message = await self._msg_repo.create(
                conversation_id=conv_id,
                role=data.role,
                content=data.content,
            )
            await self._conv_repo.increment_message_count(conv_id)
            await self._db.commit()
        except Exception as exc:
            await self._db.rollback()
            raise DatabaseError(
                message="Failed to add message",
                details={"error": str(exc)},
            ) from exc

        return MessageResponse.model_validate(message)

    async def get_messages(
        self,
        conv_id: uuid.UUID,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 50,
    ) -> MessageList:
        """List messages for a conversation with pagination.

        Messages are returned in chronological order (oldest first).

        Args:
            conv_id: The UUID of the conversation.
            user_id: The UUID of the requesting user.
            page: 1-indexed page number.
            page_size: Number of items per page (1-100).

        Returns:
            A paginated list of messages.

        Raises:
            NotFoundError: If no conversation with the given ID exists.
            AuthorizationError: If the user does not own the conversation.
        """
        conversation = await self._conv_repo.get_by_id(conv_id)
        if conversation is None or conversation.is_deleted:
            raise NotFoundError(
                message="Conversation not found",
                details={"conversation_id": str(conv_id)},
            )
        if conversation.user_id != user_id:
            raise AuthorizationError(
                message="You do not have access to this conversation",
                details={"conversation_id": str(conv_id)},
            )

        skip = (page - 1) * page_size
        items, total = await self._msg_repo.get_by_conversation(
            conversation_id=conv_id,
            skip=skip,
            limit=page_size,
        )

        return MessageList(
            items=[MessageResponse.model_validate(m) for m in items],
            total=total,
        )

    # ------------------------------------------------------------------
    # Bookmarks
    # ------------------------------------------------------------------

    async def bookmark_conversation(
        self,
        user_id: uuid.UUID,
        data: ConversationBookmarkCreate,
    ) -> ConversationBookmarkResponse:
        """Bookmark a conversation for the given user.

        Raises if the conversation does not exist, is not owned by the user,
        or is already bookmarked.

        Args:
            user_id: The UUID of the user creating the bookmark.
            data: Validated bookmark request payload.

        Returns:
            The newly created bookmark.

        Raises:
            NotFoundError: If the conversation does not exist.
            AuthorizationError: If the user does not own the conversation.
            ValidationError: If the conversation is already bookmarked.
            DatabaseError: If the underlying database operation fails.
        """
        conversation = await self._conv_repo.get_by_id(data.conversation_id)
        if conversation is None or conversation.is_deleted:
            raise NotFoundError(
                message="Conversation not found",
                details={"conversation_id": str(data.conversation_id)},
            )
        if conversation.user_id != user_id:
            raise AuthorizationError(
                message="You do not have access to this conversation",
                details={"conversation_id": str(data.conversation_id)},
            )

        existing = await self._bookmark_repo.get_by_user_and_conversation(
            user_id=user_id,
            conversation_id=data.conversation_id,
        )
        if existing is not None:
            raise ValidationError(
                message="Conversation is already bookmarked",
                details={"conversation_id": str(data.conversation_id)},
            )

        try:
            bookmark = await self._bookmark_repo.create(
                user_id=user_id,
                conversation_id=data.conversation_id,
                name=data.name,
                note=data.note,
            )
            await self._db.commit()
        except Exception as exc:
            await self._db.rollback()
            raise DatabaseError(
                message="Failed to create bookmark",
                details={"error": str(exc)},
            ) from exc

        return ConversationBookmarkResponse.model_validate(bookmark)

    async def list_bookmarks(
        self,
        user_id: uuid.UUID,
    ) -> list[ConversationBookmarkResponse]:
        """List all bookmarks for a user.

        Args:
            user_id: The UUID of the owning user.

        Returns:
            A list of bookmarks ordered by creation time (newest first).
        """
        bookmarks = await self._bookmark_repo.get_by_user(user_id=user_id)
        return [
            ConversationBookmarkResponse.model_validate(b) for b in bookmarks
        ]

    async def delete_bookmark(
        self,
        bookmark_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        """Soft-delete a bookmark with ownership check.

        Args:
            bookmark_id: The UUID of the bookmark to delete.
            user_id: The UUID of the requesting user.

        Raises:
            NotFoundError: If no bookmark with the given ID exists.
            AuthorizationError: If the user does not own the bookmark.
            DatabaseError: If the underlying database operation fails.
        """
        bookmark = await self._bookmark_repo.get_by_id(bookmark_id)
        if bookmark is None or bookmark.is_deleted:
            raise NotFoundError(
                message="Bookmark not found",
                details={"bookmark_id": str(bookmark_id)},
            )
        if bookmark.user_id != user_id:
            raise AuthorizationError(
                message="You do not have access to this bookmark",
                details={"bookmark_id": str(bookmark_id)},
            )

        try:
            await self._bookmark_repo.delete(bookmark_id, soft=True)
            await self._db.commit()
        except Exception as exc:
            await self._db.rollback()
            raise DatabaseError(
                message="Failed to delete bookmark",
                details={"error": str(exc)},
            ) from exc
