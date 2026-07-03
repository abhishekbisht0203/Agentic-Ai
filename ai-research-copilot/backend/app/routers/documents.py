"""Document management API routes."""

import io
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response

from app.database.session import get_db_session
from app.dependencies.auth import get_current_user_from_token
from app.models.user import User
from app.schemas.document import (
    DocumentChunkResponse,
    DocumentCreate,
    DocumentDetail,
    DocumentList,
    DocumentResponse,
    DocumentUpdate,
    DocumentUploadResponse,
)
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["Documents"])

CurrentUser = Annotated[User, Depends(get_current_user_from_token)]
DbSession = Annotated[AsyncSession, Depends(get_db_session)]


@router.post("/upload", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
    current_user: CurrentUser,
    db: DbSession,
    file: Annotated[UploadFile, File(description="File to upload")],
    name: Annotated[str | None, Query(description="Optional document name")] = None,
    knowledge_base_ids: Annotated[str | None, Query(description="Comma-separated knowledge base IDs")] = None,
) -> DocumentUploadResponse:
    """Upload a document file for processing."""
    file_data = await file.read()
    file_size = len(file_data)
    file_stream = io.BytesIO(file_data)

    data = None
    if name or knowledge_base_ids:
        kb_ids = None
        if knowledge_base_ids:
            kb_ids = [uuid.UUID(kid.strip()) for kid in knowledge_base_ids.split(",") if kid.strip()]
        data = DocumentCreate(name=name, knowledge_base_ids=kb_ids)

    service = DocumentService(db)
    return await service.upload_document(
        user_id=current_user.id,
        file_data=file_stream,
        filename=file.filename or "unnamed",
        content_type=file.content_type or "application/octet-stream",
        file_size=file_size,
        data=data,
    )


@router.get("/", response_model=DocumentList)
async def list_documents(
    current_user: CurrentUser,
    db: DbSession,
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
) -> DocumentList:
    """List documents for the current user with pagination."""
    service = DocumentService(db)
    return await service.list_documents(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
    )


@router.get("/{document_id}", response_model=DocumentDetail)
async def get_document(
    current_user: CurrentUser,
    db: DbSession,
    document_id: uuid.UUID,
) -> DocumentDetail:
    """Get detailed information about a document."""
    service = DocumentService(db)
    return await service.get_document(
        document_id=document_id,
        user_id=current_user.id,
    )


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    current_user: CurrentUser,
    db: DbSession,
    document_id: uuid.UUID,
    data: DocumentUpdate,
) -> DocumentResponse:
    """Update document metadata."""
    service = DocumentService(db)
    return await service.update_document(
        document_id=document_id,
        user_id=current_user.id,
        data=data,
    )


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    current_user: CurrentUser,
    db: DbSession,
    document_id: uuid.UUID,
) -> None:
    """Delete a document."""
    service = DocumentService(db)
    await service.delete_document(
        document_id=document_id,
        user_id=current_user.id,
    )


@router.get("/{document_id}/chunks", response_model=list[DocumentChunkResponse])
async def get_document_chunks(
    current_user: CurrentUser,
    db: DbSession,
    document_id: uuid.UUID,
) -> list[DocumentChunkResponse]:
    """Get all chunks for a document."""
    service = DocumentService(db)
    return await service.get_document_chunks(
        document_id=document_id,
        user_id=current_user.id,
    )


@router.get("/{document_id}/download")
async def download_document(
    current_user: CurrentUser,
    db: DbSession,
    document_id: uuid.UUID,
) -> Response:
    """Download the raw file content of a document."""
    service = DocumentService(db)
    content = await service.get_document_content(
        document_id=document_id,
        user_id=current_user.id,
    )
    doc = await service.get_document(
        document_id=document_id,
        user_id=current_user.id,
    )
    return Response(
        content=content,
        media_type=doc.mime_type,
        headers={
            "Content-Disposition": f'attachment; filename="{doc.original_filename}"'
        },
    )
