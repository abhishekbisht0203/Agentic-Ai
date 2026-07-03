"""Knowledge base management service."""

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.models.document import KnowledgeBase
from app.repositories.document import DocumentRepository
from app.repositories.knowledge_base import KnowledgeBaseRepository
from app.schemas.knowledge_base import (
    KnowledgeBaseAddDocuments,
    KnowledgeBaseCreate,
    KnowledgeBaseDetail,
    KnowledgeBaseList,
    KnowledgeBaseRemoveDocuments,
    KnowledgeBaseResponse,
    KnowledgeBaseUpdate,
)

logger = logging.getLogger(__name__)


class KnowledgeBaseService:
    """Service for knowledge base CRUD and document association."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.kb_repo = KnowledgeBaseRepository(db)
        self.doc_repo = DocumentRepository(db)

    async def create_knowledge_base(
        self,
        user_id: uuid.UUID,
        data: KnowledgeBaseCreate,
    ) -> KnowledgeBaseResponse:
        """Create a new knowledge base.

        Args:
            user_id: UUID of the owning user.
            data: Creation payload with name, description, and settings.

        Raises:
            ValidationError: If the name is empty after trimming.

        Returns:
            KnowledgeBaseResponse with the newly created knowledge base.
        """
        name = data.name.strip()
        if not name:
            raise ValidationError(message="Knowledge base name cannot be empty")

        kb = await self.kb_repo.create(
            user_id=user_id,
            name=name,
            description=data.description.strip() if data.description else None,
            embedding_model=data.embedding_model or "text-embedding-ada-002",
            is_public=data.is_public if data.is_public is not None else False,
        )

        logger.info(
            "Knowledge base created: id=%s name=%s user=%s",
            kb.id,
            kb.name,
            user_id,
        )

        return KnowledgeBaseResponse.model_validate(kb)

    async def get_knowledge_base(
        self,
        kb_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> KnowledgeBaseDetail:
        """Retrieve full details for a knowledge base.

        Args:
            kb_id: UUID of the knowledge base.
            user_id: UUID of the owning user.

        Raises:
            NotFoundError: If the knowledge base does not exist or is not owned by the user.
        """
        kb = await self._get_owned_kb(kb_id, user_id)
        return KnowledgeBaseDetail.model_validate(kb)

    async def list_knowledge_bases(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> KnowledgeBaseList:
        """Return a paginated list of the user's knowledge bases.

        Args:
            user_id: UUID of the owning user.
            page: 1-indexed page number.
            page_size: Number of items per page (max 100).
        """
        page_size = min(page_size, 100)
        skip = (page - 1) * page_size
        items, total = await self.kb_repo.get_by_user(user_id, skip, page_size)
        return KnowledgeBaseList(
            items=[KnowledgeBaseResponse.model_validate(kb) for kb in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def update_knowledge_base(
        self,
        kb_id: uuid.UUID,
        user_id: uuid.UUID,
        data: KnowledgeBaseUpdate,
    ) -> KnowledgeBaseResponse:
        """Update knowledge base metadata.

        Args:
            kb_id: UUID of the knowledge base.
            user_id: UUID of the owning user.
            data: Fields to update (name, description, is_public).

        Raises:
            NotFoundError: If the knowledge base does not exist or is not owned by the user.
            ValidationError: If the provided name is empty.
        """
        kb = await self._get_owned_kb(kb_id, user_id)

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            raise ValidationError(message="No fields provided for update")

        if "name" in update_data:
            name = update_data["name"].strip() if isinstance(update_data["name"], str) else update_data["name"]
            if not name:
                raise ValidationError(message="Knowledge base name cannot be empty")
            update_data["name"] = name

        if "description" in update_data:
            desc = update_data["description"]
            if isinstance(desc, str):
                update_data["description"] = desc.strip() if desc.strip() else None

        updated = await self.kb_repo.update(kb_id, **update_data)
        return KnowledgeBaseResponse.model_validate(updated)

    async def delete_knowledge_base(
        self,
        kb_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        """Delete a knowledge base and its document associations.

        This does not delete the associated documents themselves.

        Args:
            kb_id: UUID of the knowledge base.
            user_id: UUID of the owning user.

        Raises:
            NotFoundError: If the knowledge base does not exist or is not owned by the user.
        """
        await self._get_owned_kb(kb_id, user_id)
        await self.kb_repo.delete(kb_id)
        logger.info("Knowledge base deleted: id=%s user=%s", kb_id, user_id)

    async def add_documents(
        self,
        kb_id: uuid.UUID,
        user_id: uuid.UUID,
        doc_ids: list[uuid.UUID],
    ) -> None:
        """Add documents to a knowledge base.

        All documents must belong to the requesting user and be in 'ready'
        status. Duplicate associations are silently ignored.

        Args:
            kb_id: UUID of the knowledge base.
            user_id: UUID of the owning user.
            doc_ids: List of document UUIDs to associate.

        Raises:
            NotFoundError: If the knowledge base or any document is not found.
            ValidationError: If no document IDs are provided or a document is not ready.
        """
        if not doc_ids:
            raise ValidationError(message="At least one document ID must be provided")

        kb = await self._get_owned_kb(kb_id, user_id)

        for doc_id in doc_ids:
            doc = await self.doc_repo.get_by_id(doc_id)
            if not doc or doc.user_id != user_id:
                raise NotFoundError(
                    message=f"Document {doc_id} not found"
                )
            if doc.status != "ready":
                raise ValidationError(
                    message=f"Document {doc_id} is not ready (status: {doc.status})"
                )

        await self.kb_repo.add_documents(kb_id, doc_ids)

        logger.info(
            "Documents added to knowledge base: kb=%s docs=%s",
            kb_id,
            [str(d) for d in doc_ids],
        )

    async def remove_documents(
        self,
        kb_id: uuid.UUID,
        user_id: uuid.UUID,
        doc_ids: list[uuid.UUID],
    ) -> None:
        """Remove documents from a knowledge base.

        Removes the associations but does not delete the documents themselves.

        Args:
            kb_id: UUID of the knowledge base.
            user_id: UUID of the owning user.
            doc_ids: List of document UUIDs to disassociate.

        Raises:
            NotFoundError: If the knowledge base is not found.
            ValidationError: If no document IDs are provided.
        """
        if not doc_ids:
            raise ValidationError(message="At least one document ID must be provided")

        await self._get_owned_kb(kb_id, user_id)
        await self.kb_repo.remove_documents(kb_id, doc_ids)

        logger.info(
            "Documents removed from knowledge base: kb=%s docs=%s",
            kb_id,
            [str(d) for d in doc_ids],
        )

    async def _get_owned_kb(
        self, kb_id: uuid.UUID, user_id: uuid.UUID
    ) -> KnowledgeBase:
        """Fetch a knowledge base and verify ownership.

        Args:
            kb_id: UUID of the knowledge base.
            user_id: UUID of the owning user.

        Raises:
            NotFoundError: If the knowledge base is missing or belongs to another user.

        Returns:
            The validated KnowledgeBase model instance.
        """
        kb = await self.kb_repo.get_by_id(kb_id)
        if not kb or kb.user_id != user_id:
            raise NotFoundError(message="Knowledge base not found")
        return kb
