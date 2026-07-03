"""Document management service."""

import logging
import uuid
from typing import BinaryIO

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    DocumentProcessingError,
    NotFoundError,
    ValidationError,
)
from app.models.document import Document
from app.repositories.document import DocumentRepository
from app.repositories.knowledge_base import KnowledgeBaseRepository
from app.schemas.document import (
    DocumentChunkResponse,
    DocumentCreate,
    DocumentDetail,
    DocumentList,
    DocumentResponse,
    DocumentUpdate,
    DocumentUploadResponse,
)
from app.storage import LocalStorage, S3Storage

logger = logging.getLogger(__name__)


class DocumentService:
    """Service for document CRUD, upload, and chunk retrieval."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.doc_repo = DocumentRepository(db)
        self.kb_repo = KnowledgeBaseRepository(db)
        self.storage = self._build_storage()

    @staticmethod
    def _build_storage() -> S3Storage | LocalStorage:
        """Select storage backend from application settings."""
        backend = getattr(settings, "storage_backend", "s3")
        if backend == "local":
            return LocalStorage(
                base_path=getattr(settings, "local_storage_path", "./uploads")
            )
        return S3Storage()

    async def upload_document(
        self,
        user_id: uuid.UUID,
        file_data: BinaryIO,
        filename: str,
        content_type: str,
        file_size: int,
        data: DocumentCreate | None = None,
    ) -> DocumentUploadResponse:
        """Upload a file to storage and persist its metadata.

        Args:
            user_id: ID of the uploading user.
            file_data: Seekable binary file-like object.
            filename: Original filename including extension.
            content_type: MIME type of the file.
            file_size: Size in bytes.
            data: Optional additional metadata (name, knowledge_base_ids).

        Raises:
            DocumentProcessingError: If the storage upload fails.

        Returns:
            DocumentUploadResponse with the new document ID and status.
        """
        if file_size <= 0:
            raise ValidationError(message="File size must be greater than zero")

        if file_size > 500 * 1024 * 1024:
            raise ValidationError(message="File size exceeds the 500 MB limit")

        doc_name = (data.name if data and data.name else filename).strip()
        if not doc_name:
            raise ValidationError(message="Document name cannot be empty")

        try:
            storage_path = await self.storage.upload_file(
                file_data, filename, content_type
            )
        except Exception as exc:
            logger.exception("Storage upload failed for file %s", filename)
            raise DocumentProcessingError(
                message="Failed to upload file to storage",
                details={"filename": filename, "error": str(exc)},
            ) from exc

        doc = await self.doc_repo.create(
            user_id=user_id,
            name=doc_name,
            original_filename=filename,
            mime_type=content_type,
            file_size=file_size,
            storage_path=storage_path,
            storage_backend="s3",
            status="processing",
        )

        if data and data.knowledge_base_ids:
            for kb_id in data.knowledge_base_ids:
                kb = await self.kb_repo.get_by_id(kb_id)
                if not kb or kb.user_id != user_id:
                    raise NotFoundError(
                        message=f"Knowledge base {kb_id} not found"
                    )
            await self.kb_repo.add_documents(doc.id, data.knowledge_base_ids)

        logger.info(
            "Document uploaded: id=%s name=%s user=%s",
            doc.id,
            doc.name,
            user_id,
        )

        return DocumentUploadResponse(
            id=doc.id,
            name=doc.name,
            status=doc.status,
            message="Document uploaded successfully. Processing will begin shortly.",
        )

    async def get_document(
        self, document_id: uuid.UUID, user_id: uuid.UUID
    ) -> DocumentDetail:
        """Retrieve full details for a single document.

        Args:
            document_id: UUID of the document.
            user_id: UUID of the owning user.

        Raises:
            NotFoundError: If the document does not exist or is not owned by the user.
        """
        doc = await self._get_owned_document(document_id, user_id)
        return DocumentDetail.model_validate(doc)

    async def list_documents(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> DocumentList:
        """Return a paginated list of the user's documents.

        Args:
            user_id: UUID of the owning user.
            page: 1-indexed page number.
            page_size: Number of items per page (max 100).
        """
        page_size = min(page_size, 100)
        skip = (page - 1) * page_size
        items, total = await self.doc_repo.get_by_user(user_id, skip, page_size)
        return DocumentList(
            items=[DocumentResponse.model_validate(d) for d in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def update_document(
        self,
        document_id: uuid.UUID,
        user_id: uuid.UUID,
        data: DocumentUpdate,
    ) -> DocumentResponse:
        """Update document metadata (name).

        Args:
            document_id: UUID of the document.
            user_id: UUID of the owning user.
            data: Fields to update.

        Raises:
            NotFoundError: If the document does not exist or is not owned by the user.
            ValidationError: If the provided name is empty.
        """
        doc = await self._get_owned_document(document_id, user_id)

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            raise ValidationError(message="No fields provided for update")

        if "name" in update_data:
            name = update_data["name"].strip() if isinstance(update_data["name"], str) else update_data["name"]
            if not name:
                raise ValidationError(message="Document name cannot be empty")
            update_data["name"] = name

        updated = await self.doc_repo.update(document_id, **update_data)
        return DocumentResponse.model_validate(updated)

    async def delete_document(
        self, document_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        """Delete a document from storage and the database.

        Removes the file from storage first, then soft-deletes the database
        record. Storage deletion failures are logged but do not block the
        database deletion.

        Args:
            document_id: UUID of the document.
            user_id: UUID of the owning user.

        Raises:
            NotFoundError: If the document does not exist or is not owned by the user.
        """
        doc = await self._get_owned_document(document_id, user_id)

        try:
            await self.storage.delete_file(doc.storage_path)
        except Exception:
            logger.warning(
                "Failed to delete storage file %s for document %s",
                doc.storage_path,
                document_id,
            )

        await self.doc_repo.delete(document_id)
        logger.info("Document deleted: id=%s user=%s", document_id, user_id)

    async def get_document_chunks(
        self, document_id: uuid.UUID, user_id: uuid.UUID
    ) -> list[DocumentChunkResponse]:
        """Return all chunks belonging to a document.

        Args:
            document_id: UUID of the document.
            user_id: UUID of the owning user.

        Raises:
            NotFoundError: If the document does not exist or is not owned by the user.
        """
        doc = await self._get_owned_document(document_id, user_id)
        return [DocumentChunkResponse.model_validate(c) for c in doc.chunks]

    async def get_document_content(
        self, document_id: uuid.UUID, user_id: uuid.UUID
    ) -> bytes:
        """Download the raw file bytes for a document.

        Args:
            document_id: UUID of the document.
            user_id: UUID of the owning user.

        Raises:
            NotFoundError: If the document does not exist or is not owned by the user.
            DocumentProcessingError: If the file cannot be retrieved from storage.
        """
        doc = await self._get_owned_document(document_id, user_id)

        try:
            return await self.storage.download_file(doc.storage_path)
        except Exception as exc:
            logger.exception(
                "Failed to download file %s for document %s",
                doc.storage_path,
                document_id,
            )
            raise DocumentProcessingError(
                message="Failed to retrieve file from storage",
                details={"document_id": str(document_id), "error": str(exc)},
            ) from exc

    async def _get_owned_document(
        self, document_id: uuid.UUID, user_id: uuid.UUID
    ) -> Document:
        """Fetch a document and verify ownership.

        Args:
            document_id: UUID of the document.
            user_id: UUID of the owning user.

        Raises:
            NotFoundError: If the document is missing or belongs to another user.

        Returns:
            The validated Document model instance.
        """
        doc = await self.doc_repo.get_by_id(document_id)
        if not doc or doc.user_id != user_id:
            raise NotFoundError(message="Document not found")
        return doc
