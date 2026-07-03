"""
Main RAG pipeline orchestrator.

Coordinates document ingestion (loading, chunking, embedding, storing)
and query processing (embedding, retrieval, reranking, generation).
"""

import logging
import uuid
from typing import Any

from app.core.config.settings import settings
from app.rag.chunking.base import BaseChunker, Chunk
from app.rag.embeddings.embedder import EmbeddingService
from app.rag.generator.generator import RAGGenerator
from app.rag.loaders.base import BaseDocumentLoader
from app.rag.reranker.cross_encoder import CrossEncoderReranker
from app.rag.retriever.retriever import HybridRetriever
from app.rag.vectorstore.qdrant_store import QdrantVectorStore

logger = logging.getLogger(__name__)


class RAGPipeline:
    """End-to-end RAG pipeline.

    Manages the full lifecycle of document ingestion and query
    processing for the AI Research Copilot's knowledge base system.
    """

    def __init__(self, user_id: uuid.UUID, knowledge_base_id: uuid.UUID):
        """Initialize the RAG pipeline.

        Args:
            user_id: The owning user's UUID.
            knowledge_base_id: The knowledge base UUID used for collection naming.
        """
        self.user_id = user_id
        self.knowledge_base_id = knowledge_base_id

        collection_name = f"kb_{knowledge_base_id}"

        self.embedder = EmbeddingService(
            model_name=settings.llm.openai_embedding_model
        )
        self.vector_store = QdrantVectorStore(
            collection_name=collection_name,
            host=settings.qdrant.host,
            port=settings.qdrant.port,
            api_key=settings.qdrant.api_key,
            prefer_grpc=settings.qdrant.prefer_grpc,
        )
        self.retriever = HybridRetriever(
            vector_store=self.vector_store, embedder=self.embedder
        )
        self.reranker = CrossEncoderReranker()

        self._collection_initialized = False

    async def _ensure_collection(self) -> None:
        """Ensure the Qdrant collection exists, creating it if needed."""
        if self._collection_initialized:
            return
        dimension = self.embedder.get_dimension()
        await self.vector_store.create_collection(dimension)
        self._collection_initialized = True

    async def ingest_document(
        self,
        document_id: uuid.UUID,
        content: bytes,
        filename: str,
        content_type: str,
        chunk_strategy: str = "recursive",
        **chunk_kwargs: Any,
    ) -> dict:
        """Ingest a document into the vector store.

        Full pipeline: load text, chunk, embed, and store vectors.

        Args:
            document_id: UUID of the document being ingested.
            content: Raw file bytes.
            filename: Original filename (used for loader detection).
            content_type: MIME type of the file.
            chunk_strategy: Chunking strategy name ('recursive', 'semantic', 'parent_child').
            **chunk_kwargs: Additional arguments for the chunker.

        Returns:
            Dict with 'document_id', 'chunk_count', and 'status' keys.

        Raises:
            ValueError: If the document cannot be loaded or chunked.
        """
        logger.info(
            "Ingesting document '%s' (id=%s, type=%s)",
            filename,
            document_id,
            content_type,
        )

        await self._ensure_collection()

        loader = BaseDocumentLoader.detect_loader(filename, content_type)
        text = await loader.load(content, filename)
        logger.debug("Loaded %d characters from '%s'", len(text), filename)

        chunker = BaseChunker.create_chunker(chunk_strategy, **chunk_kwargs)
        chunks = chunker.chunk(text)
        logger.debug("Produced %d chunks from '%s'", len(chunks), filename)

        if not chunks:
            raise ValueError(f"No chunks produced from document '{filename}'")

        chunk_texts = [c.content for c in chunks]
        embeddings = await self.embedder.embed_batch(chunk_texts)

        points: list[dict] = []
        for chunk, embedding in zip(chunks, embeddings):
            point_id = str(uuid.uuid4())
            points.append({
                "id": point_id,
                "vector": embedding,
                "payload": {
                    "document_id": str(document_id),
                    "knowledge_base_id": str(self.knowledge_base_id),
                    "user_id": str(self.user_id),
                    "chunk_index": chunk.chunk_index,
                    "content": chunk.content,
                    "token_count": chunk.token_count,
                    "chunk_type": chunk.chunk_type,
                    "filename": filename,
                    "metadata": chunk.metadata or {},
                },
            })

        await self.vector_store.upsert(points)

        result = {
            "document_id": str(document_id),
            "chunk_count": len(chunks),
            "points_stored": len(points),
            "status": "completed",
        }
        logger.info(
            "Ingestion complete for '%s': %d chunks stored", filename, len(points)
        )
        return result

    async def query(
        self,
        query: str,
        top_k: int = 5,
        filters: dict | None = None,
    ) -> list[dict]:
        """Query the knowledge base.

        Full pipeline: embed query, search, rerank, return.

        Args:
            query: The user's question.
            top_k: Number of results to return.
            filters: Optional metadata filters.

        Returns:
            Ranked list of chunk dicts with scores.
        """
        logger.info("Querying KB '%s': '%s'", self.knowledge_base_id, query[:80])

        results = await self.retriever.retrieve(query, top_k=top_k, filters=filters)

        if not results:
            logger.info("No results found for query")
            return []

        reranked = await self.reranker.rerank(
            query, results, top_k=min(top_k, len(results))
        )

        logger.info("Returning %d reranked results", len(reranked))
        return reranked

    async def generate_response(
        self,
        query: str,
        top_k: int = 5,
        llm_provider: Any = None,
    ) -> dict:
        """Generate a full RAG response with citations.

        Args:
            query: The user's question.
            top_k: Number of chunks to retrieve.
            llm_provider: LLM provider for generation. If None, returns
                          retrieved chunks only.

        Returns:
            Dict with 'response' and 'citations' keys.
        """
        results = await self.query(query, top_k=top_k)

        if not results:
            return {
                "response": "No relevant documents found.",
                "citations": [],
            }

        if llm_provider is None:
            context_parts = []
            for i, r in enumerate(results, 1):
                payload = r.get("payload", r)
                content = payload.get("content", "")
                context_parts.append(f"[{i}] {content}")
            return {
                "response": "\n\n".join(context_parts),
                "citations": [],
            }

        generator = RAGGenerator(
            llm_provider=llm_provider,
            retriever=self.retriever,
            reranker=self.reranker,
        )
        return await generator.generate(query, top_k=top_k)

    async def delete_document(self, document_id: uuid.UUID) -> None:
        """Remove all chunks for a document from the vector store.

        Args:
            document_id: The document UUID to delete.
        """
        logger.info("Deleting document '%s' from KB '%s'", document_id, self.knowledge_base_id)
        await self.vector_store.delete_by_document(document_id)
        logger.info("Deleted all chunks for document '%s'", document_id)

    async def delete_all(self) -> None:
        """Delete the entire collection from the vector store."""
        logger.warning(
            "Deleting entire collection for KB '%s'", self.knowledge_base_id
        )
        await self.vector_store.delete_collection()
        self._collection_initialized = False

    async def get_stats(self) -> dict:
        """Return statistics about the knowledge base collection.

        Returns:
            Dict with collection metadata.
        """
        await self._ensure_collection()
        info = await self.vector_store.get_collection_info()
        return {
            "knowledge_base_id": str(self.knowledge_base_id),
            "user_id": str(self.user_id),
            "collection_name": f"kb_{self.knowledge_base_id}",
            **info,
        }
