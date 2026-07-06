"""Document management service."""

import io
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
from app.models.document import Document, DocumentChunk
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


def _extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text content from a PDF file."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(file_bytes))
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text.strip())
        return "\n\n".join(pages)
    except Exception as exc:
        logger.warning("PDF extraction failed: %s", exc)
        return ""


def _extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text content from a DOCX file."""
    try:
        import docx
        doc = docx.Document(io.BytesIO(file_bytes))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n\n".join(paragraphs)
    except Exception as exc:
        logger.warning("DOCX extraction failed: %s", exc)
        return ""


def _extract_text_from_plain(file_bytes: bytes, encoding: str = "utf-8") -> str:
    """Decode plain text from bytes."""
    try:
        return file_bytes.decode(encoding)
    except UnicodeDecodeError:
        return file_bytes.decode("utf-8", errors="replace")


def _extract_text(file_bytes: bytes, mime_type: str, filename: str) -> str:
    """Route to the appropriate text extractor based on MIME type."""
    if mime_type == "application/pdf" or filename.lower().endswith(".pdf"):
        return _extract_text_from_pdf(file_bytes)
    if mime_type in (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
    ) or filename.lower().endswith((".docx", ".doc")):
        return _extract_text_from_docx(file_bytes)
    return _extract_text_from_plain(file_bytes)


def _chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    """Split text into overlapping chunks."""
    if not text or not text.strip():
        return []
    chunks: list[str] = []
    start = 0
    text_length = len(text)
    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= text_length:
            break
        start = end - overlap
        if start < 0:
            start = 0
    return chunks


def _estimate_token_count(text: str) -> int:
    """Estimate token count (~4 chars per token)."""
    return len(text) // 4


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
        if backend == "local" or S3Storage is None:
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
        """Upload a file, extract text, create chunks, and persist metadata.

        This performs synchronous document processing so the document is
        immediately available for LLM context (like ChatGPT/Claude).
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

        # Read file bytes for text extraction
        file_data.seek(0)
        file_bytes = file_data.read()

        # Extract text synchronously
        content_text = ""
        status = "ready"
        processing_error = None
        try:
            content_text = _extract_text(file_bytes, content_type, filename)
            if not content_text.strip():
                logger.warning("No text extracted from %s", filename)
                processing_error = "No text content could be extracted from this file."
        except Exception as exc:
            logger.exception("Text extraction failed for %s", filename)
            processing_error = f"Text extraction failed: {exc}"
            status = "ready"

        # Create chunks from extracted text
        chunks_data = _chunk_text(content_text) if content_text.strip() else []

        # Create the document record
        doc = await self.doc_repo.create(
            user_id=user_id,
            name=doc_name,
            original_filename=filename,
            mime_type=content_type,
            file_size=file_size,
            storage_path=storage_path,
            storage_backend="local",
            status=status,
            content_text=content_text if content_text.strip() else None,
            chunk_count=len(chunks_data),
            processing_error=processing_error,
            conversation_id=data.conversation_id if data else None,
        )

        # Create chunk records in the database
        for idx, chunk_content in enumerate(chunks_data):
            chunk = DocumentChunk(
                document_id=doc.id,
                chunk_index=idx,
                content=chunk_content,
                token_count=_estimate_token_count(chunk_content),
                chunk_type="recursive",
            )
            self.db.add(chunk)

        await self.db.flush()

        # Associate with knowledge bases if requested
        if data and data.knowledge_base_ids:
            for kb_id in data.knowledge_base_ids:
                kb = await self.kb_repo.get_by_id(kb_id)
                if not kb or kb.user_id != user_id:
                    raise NotFoundError(
                        message=f"Knowledge base {kb_id} not found"
                    )
            await self.kb_repo.add_documents(doc.id, data.knowledge_base_ids)

        logger.info(
            "Document uploaded and processed: id=%s name=%s chunks=%d user=%s",
            doc.id,
            doc.name,
            len(chunks_data),
            user_id,
        )

        return DocumentUploadResponse(
            id=doc.id,
            name=doc.name,
            status=doc.status,
            message="Document uploaded and processed successfully.",
        )

    async def get_document(
        self, document_id: uuid.UUID, user_id: uuid.UUID
    ) -> DocumentDetail:
        """Retrieve full details for a single document."""
        doc = await self._get_owned_document(document_id, user_id)
        return DocumentDetail.model_validate(doc)

    async def list_documents(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> DocumentList:
        """Return a paginated list of the user's documents."""
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
        """Update document metadata (name)."""
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
        """Delete a document from storage and the database."""
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
        """Return all chunks belonging to a document."""
        doc = await self._get_owned_document(document_id, user_id)
        return [DocumentChunkResponse.model_validate(c) for c in doc.chunks]

    async def get_document_content(
        self, document_id: uuid.UUID, user_id: uuid.UUID
    ) -> bytes:
        """Download the raw file bytes for a document."""
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
        """Fetch a document and verify ownership."""
        doc = await self.doc_repo.get_by_id(document_id)
        if not doc or doc.user_id != user_id:
            raise NotFoundError(message="Document not found")
        return doc
