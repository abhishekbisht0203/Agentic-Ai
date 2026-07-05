"""Chat and conversation API routes."""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.dependencies.auth import get_current_user_from_token
from app.models.user import User
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
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
from app.services.agent_service import AgentService
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["Chat"])


async def _get_chat_service(db: AsyncSession = Depends(get_db_session)) -> ChatService:
    """Create a ChatService instance bound to the request-scoped DB session."""
    return ChatService(db)


async def _get_agent_service(db: AsyncSession = Depends(get_db_session)) -> AgentService:
    """Create an AgentService instance bound to the request-scoped DB session."""
    return AgentService(db)


# ------------------------------------------------------------------
# Conversation CRUD
# ------------------------------------------------------------------


@router.post(
    "/conversations",
    response_model=ConversationResponse,
    status_code=201,
    summary="Create a new conversation",
)
async def create_conversation(
    data: ConversationCreate,
    current_user: User = Depends(get_current_user_from_token),
    chat_service: ChatService = Depends(_get_chat_service),
) -> ConversationResponse:
    """Create a new conversation for the authenticated user."""
    return await chat_service.create_conversation(user_id=current_user.id, data=data)


@router.get(
    "/conversations",
    response_model=ConversationList,
    summary="List conversations",
)
async def list_conversations(
    current_user: User = Depends(get_current_user_from_token),
    chat_service: ChatService = Depends(_get_chat_service),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> ConversationList:
    """Return a paginated list of conversations owned by the authenticated user."""
    return await chat_service.list_conversations(
        user_id=current_user.id, page=page, page_size=page_size
    )


@router.get(
    "/conversations/{conv_id}",
    response_model=ConversationDetail,
    summary="Get conversation detail",
)
async def get_conversation(
    conv_id: uuid.UUID,
    current_user: User = Depends(get_current_user_from_token),
    chat_service: ChatService = Depends(_get_chat_service),
) -> ConversationDetail:
    """Retrieve full details for a single conversation."""
    return await chat_service.get_conversation(conv_id=conv_id, user_id=current_user.id)


@router.put(
    "/conversations/{conv_id}",
    response_model=ConversationResponse,
    summary="Update a conversation",
)
async def update_conversation(
    conv_id: uuid.UUID,
    data: ConversationUpdate,
    current_user: User = Depends(get_current_user_from_token),
    chat_service: ChatService = Depends(_get_chat_service),
) -> ConversationResponse:
    """Update conversation metadata (title, description, status)."""
    return await chat_service.update_conversation(
        conv_id=conv_id, user_id=current_user.id, data=data
    )


@router.delete(
    "/conversations/{conv_id}",
    status_code=204,
    summary="Delete a conversation",
)
async def delete_conversation(
    conv_id: uuid.UUID,
    current_user: User = Depends(get_current_user_from_token),
    chat_service: ChatService = Depends(_get_chat_service),
) -> None:
    """Soft-delete a conversation and all its messages."""
    await chat_service.delete_conversation(conv_id=conv_id, user_id=current_user.id)


# ------------------------------------------------------------------
# Messages
# ------------------------------------------------------------------


@router.post(
    "/conversations/{conv_id}/messages",
    response_model=MessageResponse,
    status_code=201,
    summary="Add a message to a conversation",
)
async def add_message(
    conv_id: uuid.UUID,
    data: MessageCreate,
    current_user: User = Depends(get_current_user_from_token),
    chat_service: ChatService = Depends(_get_chat_service),
) -> MessageResponse:
    """Append a message to an existing conversation."""
    return await chat_service.add_message(
        conv_id=conv_id, user_id=current_user.id, data=data
    )


@router.get(
    "/conversations/{conv_id}/messages",
    response_model=MessageList,
    summary="List messages in a conversation",
)
async def get_messages(
    conv_id: uuid.UUID,
    current_user: User = Depends(get_current_user_from_token),
    chat_service: ChatService = Depends(_get_chat_service),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
) -> MessageList:
    """Return a paginated list of messages for a conversation (oldest first)."""
    return await chat_service.get_messages(
        conv_id=conv_id, user_id=current_user.id, page=page, page_size=page_size
    )


# ------------------------------------------------------------------
# Bookmarks
# ------------------------------------------------------------------


@router.post(
    "/bookmarks",
    response_model=ConversationBookmarkResponse,
    status_code=201,
    summary="Bookmark a conversation",
)
async def bookmark_conversation(
    data: ConversationBookmarkCreate,
    current_user: User = Depends(get_current_user_from_token),
    chat_service: ChatService = Depends(_get_chat_service),
) -> ConversationBookmarkResponse:
    """Create a bookmark for a conversation."""
    return await chat_service.bookmark_conversation(user_id=current_user.id, data=data)


@router.get(
    "/bookmarks",
    response_model=list[ConversationBookmarkResponse],
    summary="List bookmarks",
)
async def list_bookmarks(
    current_user: User = Depends(get_current_user_from_token),
    chat_service: ChatService = Depends(_get_chat_service),
) -> list[ConversationBookmarkResponse]:
    """Return all bookmarks for the authenticated user (newest first)."""
    return await chat_service.list_bookmarks(user_id=current_user.id)


@router.delete(
    "/bookmarks/{bookmark_id}",
    status_code=204,
    summary="Delete a bookmark",
)
async def delete_bookmark(
    bookmark_id: uuid.UUID,
    current_user: User = Depends(get_current_user_from_token),
    chat_service: ChatService = Depends(_get_chat_service),
) -> None:
    """Soft-delete a bookmark."""
    await chat_service.delete_bookmark(bookmark_id=bookmark_id, user_id=current_user.id)


# ------------------------------------------------------------------
# Chat send
# ------------------------------------------------------------------


@router.post(
    "/send",
    response_model=ChatResponse,
    summary="Send a chat message and get an agent response",
)
async def send_chat(
    data: ChatRequest,
    current_user: User = Depends(get_current_user_from_token),
    chat_service: ChatService = Depends(_get_chat_service),
    agent_service: AgentService = Depends(_get_agent_service),
) -> ChatResponse:
    """Send a user message, invoke the agent, and return the response."""
    from app.schemas.agent import AgentExecuteRequest

    conv_id = data.conversation_id
    if conv_id is None:
        from app.schemas.chat import ConversationCreate

        new_conv = await chat_service.create_conversation(
            user_id=current_user.id,
            data=ConversationCreate(
                agent_type=data.agent_type,
                knowledge_base_id=data.knowledge_base_id,
            ),
        )
        conv_id = new_conv.id

    user_message = await chat_service.add_message(
        conv_id=conv_id,
        user_id=current_user.id,
        data=MessageCreate(content=data.message, role="user"),
    )

    agent_request = AgentExecuteRequest(
        agent_type=data.agent_type or "research",
        input_data={"message": data.message},
        conversation_id=conv_id,
        model=data.model,
    )
    agent_response = await agent_service.execute_agent(
        user_id=current_user.id, data=agent_request
    )

    assistant_content = agent_response.output_data.get("response", "") if agent_response.output_data else ""
    assistant_message = await chat_service.add_message(
        conv_id=conv_id,
        user_id=current_user.id,
        data=MessageCreate(content=assistant_content, role="assistant"),
    )

    return ChatResponse(
        conversation_id=conv_id,
        message=assistant_message,
        citations=agent_response.output_data.get("citations", []) if agent_response.output_data else [],
    )
