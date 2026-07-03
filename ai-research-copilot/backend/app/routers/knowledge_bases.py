"""Knowledge base management API routes."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.dependencies.auth import get_current_user_from_token
from app.models.user import User
from app.schemas.knowledge_base import (
    KnowledgeBaseAddDocuments,
    KnowledgeBaseCreate,
    KnowledgeBaseDetail,
    KnowledgeBaseList,
    KnowledgeBaseRemoveDocuments,
    KnowledgeBaseResponse,
    KnowledgeBaseUpdate,
)
from app.services.knowledge_base_service import KnowledgeBaseService

router = APIRouter(prefix="/knowledge-bases", tags=["Knowledge Bases"])

CurrentUser = Annotated[User, Depends(get_current_user_from_token)]
DbSession = Annotated[AsyncSession, Depends(get_db_session)]


@router.post("/", response_model=KnowledgeBaseResponse, status_code=201)
async def create_knowledge_base(
    current_user: CurrentUser,
    db: DbSession,
    data: KnowledgeBaseCreate,
) -> KnowledgeBaseResponse:
    """Create a new knowledge base."""
    service = KnowledgeBaseService(db)
    return await service.create_knowledge_base(
        user_id=current_user.id,
        data=data,
    )


@router.get("/", response_model=KnowledgeBaseList)
async def list_knowledge_bases(
    current_user: CurrentUser,
    db: DbSession,
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
) -> KnowledgeBaseList:
    """List knowledge bases for the current user with pagination."""
    service = KnowledgeBaseService(db)
    return await service.list_knowledge_bases(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
    )


@router.get("/{kb_id}", response_model=KnowledgeBaseDetail)
async def get_knowledge_base(
    current_user: CurrentUser,
    db: DbSession,
    kb_id: uuid.UUID,
) -> KnowledgeBaseDetail:
    """Get detailed information about a knowledge base."""
    service = KnowledgeBaseService(db)
    return await service.get_knowledge_base(
        kb_id=kb_id,
        user_id=current_user.id,
    )


@router.put("/{kb_id}", response_model=KnowledgeBaseResponse)
async def update_knowledge_base(
    current_user: CurrentUser,
    db: DbSession,
    kb_id: uuid.UUID,
    data: KnowledgeBaseUpdate,
) -> KnowledgeBaseResponse:
    """Update knowledge base metadata."""
    service = KnowledgeBaseService(db)
    return await service.update_knowledge_base(
        kb_id=kb_id,
        user_id=current_user.id,
        data=data,
    )


@router.delete("/{kb_id}", status_code=204)
async def delete_knowledge_base(
    current_user: CurrentUser,
    db: DbSession,
    kb_id: uuid.UUID,
) -> None:
    """Delete a knowledge base."""
    service = KnowledgeBaseService(db)
    await service.delete_knowledge_base(
        kb_id=kb_id,
        user_id=current_user.id,
    )


@router.post("/{kb_id}/documents", status_code=200)
async def add_documents(
    current_user: CurrentUser,
    db: DbSession,
    kb_id: uuid.UUID,
    data: KnowledgeBaseAddDocuments,
) -> dict[str, str]:
    """Add documents to a knowledge base."""
    service = KnowledgeBaseService(db)
    await service.add_documents(
        kb_id=kb_id,
        user_id=current_user.id,
        doc_ids=data.document_ids,
    )
    return {"message": "Documents added successfully"}


@router.delete("/{kb_id}/documents", status_code=200)
async def remove_documents(
    current_user: CurrentUser,
    db: DbSession,
    kb_id: uuid.UUID,
    data: KnowledgeBaseRemoveDocuments,
) -> dict[str, str]:
    """Remove documents from a knowledge base."""
    service = KnowledgeBaseService(db)
    await service.remove_documents(
        kb_id=kb_id,
        user_id=current_user.id,
        doc_ids=data.document_ids,
    )
    return {"message": "Documents removed successfully"}
