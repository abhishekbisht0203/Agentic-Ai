"""Chat and conversation API routes."""

import json
import uuid
import logging

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
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
from app.services.chat_service import ChatService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


async def _get_chat_service(db: AsyncSession = Depends(get_db_session)) -> ChatService:
    """Create a ChatService instance bound to the request-scoped DB session."""
    return ChatService(db)


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
    logger.info(
        "Listing conversations for user %s (page=%d, page_size=%d)",
        current_user.id, page, page_size
    )
    try:
        result = await chat_service.list_conversations(
            user_id=current_user.id, page=page, page_size=page_size
        )
        logger.info(
            "Listed %d conversations for user %s (total=%d)",
            len(result.items), current_user.id, result.total
        )
        return result
    except Exception as e:
        logger.exception(
            "Failed to list conversations for user %s: %s",
            current_user.id, str(e)
        )
        raise


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
# Helpers
# ------------------------------------------------------------------


def _get_llm_provider():
    """Get the best available LLM provider (opencode > openai > anthropic)."""
    from app.llms.factory import LLMFactory

    factory = LLMFactory(default_provider="opencode")

    # Try providers in priority order, catch init errors
    for provider_name in ["opencode", "openai", "anthropic"]:
        try:
            provider = factory.get_provider(provider_name)
            logger.info("Using LLM provider: %s", provider_name)
            return provider
        except Exception as exc:
            logger.warning("Provider '%s' failed to init: %s", provider_name, exc)
            continue

    raise ValueError(
        "No LLM provider configured. Set OPENCODE_API_KEY in your .env file. "
        "Get a free key at https://opencode.ai/zen"
    )


async def _load_conversation_history(
    chat_service: "ChatService",
    conv_id: uuid.UUID,
    user_id: uuid.UUID,
    max_messages: int = 50,
) -> list[dict[str, str]]:
    """Load recent conversation messages from DB for LLM context."""
    msg_list = await chat_service.get_messages(
        conv_id=conv_id, user_id=user_id, page=1, page_size=max_messages
    )
    history = []
    for msg in msg_list.items:
        history.append({"role": msg.role, "content": msg.content})
    return history


async def _load_conversation_documents(
    db: AsyncSession,
    conv_id: uuid.UUID,
    user_id: uuid.UUID,
) -> str:
    """Load all documents attached to a conversation and build context string.

    Returns a formatted string containing all document content for injection
    into the LLM system prompt (like ChatGPT/Claude/NotebookLM).
    """
    from app.repositories.document import DocumentRepository

    doc_repo = DocumentRepository(db)
    documents = await doc_repo.get_by_conversation(conv_id, user_id)

    if not documents:
        return ""

    doc_parts = []
    for doc in documents:
        if doc.status != "ready":
            continue
        # Prefer content_text (full extracted text), fallback to chunks
        text_content = doc.content_text
        if not text_content and doc.chunks:
            text_content = "\n\n".join(
                chunk.content for chunk in doc.chunks if chunk.content
            )
        if text_content:
            doc_parts.append(
                f"--- Document: {doc.name} ({doc.original_filename}) ---\n"
                f"{text_content}\n"
                f"--- End of Document: {doc.name} ---"
            )

    if not doc_parts:
        return ""

    context = (
        "\n\nThe user has uploaded the following documents to this conversation. "
        "Use the content from these documents when answering the user's questions.\n\n"
        + "\n\n".join(doc_parts)
    )

    logger.info(
        "Loaded document context for conversation %s: %d documents, ~%d chars",
        conv_id,
        len(doc_parts),
        len(context),
    )
    return context


# ------------------------------------------------------------------
# Chat send (non-streaming)
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
) -> ChatResponse:
    """Send a user message, invoke the LLM, and return the response."""
    from app.llms.chains.conversation import ConversationChain, ChainConfig
    from app.llms.prompts.templates import get_prompt

    import asyncio

    conv_id = data.conversation_id
    if conv_id is None:
        new_conv = await chat_service.create_conversation(
            user_id=current_user.id,
            data=ConversationCreate(
                title=data.message[:100],
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

    agent_type = data.agent_type or "general"
    system_prompt = get_prompt(agent_type)

    # Parallelize independent I/O: load history + documents
    history_task = asyncio.create_task(
        _load_conversation_history(chat_service, conv_id, current_user.id)
    )
    doc_task = asyncio.create_task(
        _load_conversation_documents(chat_service._db, conv_id, current_user.id)
    )

    try:
        provider = _get_llm_provider()
    except ValueError as exc:
        raise ValueError(str(exc))

    history, doc_context = await asyncio.gather(history_task, doc_task)

    chain_config = ChainConfig(
        system_prompt=system_prompt,
        temperature=0.7,
        max_tokens=4096,
        model=data.model,
        rag_context=doc_context if doc_context else None,
    )
    chain = ConversationChain(llm_provider=provider, config=chain_config)

    for msg in history[:-1]:
        chain.get_memory(str(conv_id)).add(msg["role"], msg["content"])

    response = await chain.predict(
        user_input=data.message,
        conversation_id=conv_id,
    )

    assistant_content = response.content
    assistant_message = await chat_service.add_message(
        conv_id=conv_id,
        user_id=current_user.id,
        data=MessageCreate(content=assistant_content, role="assistant"),
    )

    return ChatResponse(
        conversation_id=conv_id,
        message=assistant_message,
        citations=[],
    )


# ------------------------------------------------------------------
# Chat send (streaming)
# ------------------------------------------------------------------


@router.post(
    "/send-stream",
    summary="Send a chat message and stream the AI response",
)
async def send_chat_stream(
    data: ChatRequest,
    current_user: User = Depends(get_current_user_from_token),
    chat_service: ChatService = Depends(_get_chat_service),
) -> StreamingResponse:
    """Send a user message and stream the AI response token by token."""
    from app.llms.chains.conversation import ConversationChain, ChainConfig
    from app.llms.prompts.templates import get_prompt

    import asyncio

    conv_id = data.conversation_id
    if conv_id is None:
        new_conv = await chat_service.create_conversation(
            user_id=current_user.id,
            data=ConversationCreate(
                title=data.message[:100],
                agent_type=data.agent_type,
                knowledge_base_id=data.knowledge_base_id,
            ),
        )
        conv_id = new_conv.id

    # Fire-and-forget: save user message in background while we prepare
    await chat_service.add_message(
        conv_id=conv_id,
        user_id=current_user.id,
        data=MessageCreate(content=data.message, role="user"),
    )

    agent_type = data.agent_type or "general"
    system_prompt = get_prompt(agent_type)

    # Parallelize independent I/O: load history + documents + provider init
    history_task = asyncio.create_task(
        _load_conversation_history(chat_service, conv_id, current_user.id)
    )
    doc_task = asyncio.create_task(
        _load_conversation_documents(chat_service._db, conv_id, current_user.id)
    )

    # Start provider init in parallel too (may involve API key validation)
    try:
        provider = _get_llm_provider()
    except ValueError as exc:
        async def error_gen():
            yield f"data: {json.dumps({'error': str(exc), 'done': True})}\n\n"
        return StreamingResponse(
            error_gen(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "Access-Control-Allow-Origin": "*",
            },
        )

    # Await parallel tasks
    history, doc_context = await asyncio.gather(history_task, doc_task)

    chain_config = ChainConfig(
        system_prompt=system_prompt,
        temperature=0.7,
        max_tokens=4096,
        model=data.model,
        rag_context=doc_context if doc_context else None,
    )
    chain = ConversationChain(llm_provider=provider, config=chain_config)

    for msg in history[:-1]:
        chain.get_memory(str(conv_id)).add(msg["role"], msg["content"])

    async def event_generator():
        full_response = []
        client_disconnected = False
        try:
            async for chunk in chain.predict_stream(
                user_input=data.message,
                conversation_id=conv_id,
            ):
                full_response.append(chunk)
                yield f"data: {json.dumps({'content': chunk, 'done': False})}\n\n"
        except Exception as e:
            # Client disconnect or stream error — do NOT persist the assistant message.
            # The stream was interrupted, so the response is incomplete.
            client_disconnected = True
            logger.warning(
                "Stream interrupted for conversation %s: %s", conv_id, e
            )

        # Only persist the assistant message if the stream completed successfully
        # (i.e. the client did not disconnect mid-stream).
        if not client_disconnected and full_response:
            assistant_content = "".join(full_response)
            try:
                # Create a fresh DB session — the request-scoped session is already
                # closed by the time the stream finishes.
                from app.database.session import async_session_factory
                async with async_session_factory() as stream_db:
                    stream_chat_service = ChatService(stream_db)
                    await stream_chat_service.add_message(
                        conv_id=conv_id,
                        user_id=current_user.id,
                        data=MessageCreate(content=assistant_content, role="assistant"),
                    )
                yield f"data: {json.dumps({'content': '', 'done': True, 'conversation_id': str(conv_id)})}\n\n"
            except Exception as e:
                logger.error("Failed to persist assistant message: %s", e)
                yield f"data: {json.dumps({'error': 'Failed to save response', 'done': True})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        },
    )
