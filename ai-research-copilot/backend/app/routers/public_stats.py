"""Public stats and demo router - no authentication required."""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.database.session import get_db_session
from app.models.user import User
from app.models.document import Document, KnowledgeBase
from app.models.conversation import Conversation, Message
from app.models.workflow import Workflow, AgentConfiguration
from app.llms.factory import LLMFactory
from app.llms.chains.conversation import ConversationChain
from app.llms.memory.chat_memory import ChatMemory

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Public"])

DEMO_RATE_LIMIT = 5
_demo_usage: dict[str, list[float]] = {}

class DemoChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)
    history: list[dict] = Field(default_factory=list)


@router.get("/stats/public")
async def get_public_stats(
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Get aggregate platform statistics for the landing page (no auth)."""
    try:
        user_count_q = select(func.count()).select_from(User).where(User.is_active == True)
        doc_count_q = select(func.count()).select_from(Document).where(Document.is_deleted == False)
        kb_count_q = select(func.count()).select_from(KnowledgeBase).where(KnowledgeBase.is_deleted == False)
        conv_count_q = select(func.count()).select_from(Conversation).where(Conversation.is_deleted == False)
        msg_count_q = select(func.count()).select_from(Message).where(Message.is_deleted == False)
        agent_count_q = select(func.count()).select_from(AgentConfiguration).where(AgentConfiguration.is_deleted == False)
        workflow_count_q = select(func.count()).select_from(Workflow).where(Workflow.is_deleted == False)

        user_count = (await db.execute(user_count_q)).scalar() or 0
        doc_count = (await db.execute(doc_count_q)).scalar() or 0
        kb_count = (await db.execute(kb_count_q)).scalar() or 0
        conv_count = (await db.execute(conv_count_q)).scalar() or 0
        msg_count = (await db.execute(msg_count_q)).scalar() or 0
        agent_count = (await db.execute(agent_count_q)).scalar() or 0
        workflow_count = (await db.execute(workflow_count_q)).scalar() or 0

        return {
            "users": user_count,
            "documents": doc_count,
            "queries": msg_count,
            "conversations": conv_count,
            "knowledgeBases": kb_count,
            "agents": agent_count,
            "workflows": workflow_count,
            "uptime": 99.9,
        }
    except Exception as e:
        logger.warning("Failed to fetch public stats: %s", e)
        return {
            "users": 0,
            "documents": 0,
            "queries": 0,
            "conversations": 0,
            "knowledgeBases": 0,
            "agents": 0,
            "workflows": 0,
            "uptime": 99.9,
        }


@router.post("/chat/demo")
async def demo_chat(
    data: DemoChatRequest,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> Any:
    """Public demo chat endpoint with IP-based rate limiting."""
    ip = request.client.host if request.client else "unknown"
    now = datetime.now(timezone.utc).timestamp()

    usage = _demo_usage.setdefault(ip, [])
    cutoff = now - 3600
    recent = [t for t in usage if t > cutoff]
    if len(recent) >= DEMO_RATE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail="Demo rate limit reached. Please sign up for unlimited access.",
        )
    recent.append(now)
    _demo_usage[ip] = recent

    try:
        factory = LLMFactory()
        provider = factory.get_provider("opencode")
        model = provider._default_model
        memory = ChatMemory(max_tokens=2000)

        for msg in data.history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "assistant":
                memory.add_ai_message(content)
            else:
                memory.add_user_message(content)

        chain = ConversationChain(
            llm_provider=provider,
            model=model,
            memory=memory,
        )

        response = await chain.predict(data.message)

        return {
            "content": response,
            "model": model,
        }
    except Exception as e:
        logger.warning("Demo chat error: %s", e)
        return {
            "content": "I'm a demo assistant. I can give simple responses without a live LLM connection. Sign up for the full experience with GPT-4o, Claude 3.5, and more!",
            "model": "demo",
        }
