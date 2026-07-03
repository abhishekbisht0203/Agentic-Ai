"""
Qdrant vector store implementation.

Provides async-compatible wrapper around the Qdrant client for
collection management, upsert, search, and delete operations.
"""

import asyncio
import logging
import uuid
from functools import partial

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointIdsList,
    PointStruct,
    VectorParams,
)

logger = logging.getLogger(__name__)


class QdrantVectorStore:
    """Async-compatible Qdrant vector store.

    Wraps the synchronous Qdrant client with ``run_in_executor`` calls
    so all public methods can be ``await``-ed from async code.
    """

    def __init__(
        self,
        collection_name: str,
        host: str = "localhost",
        port: int = 6333,
        api_key: str | None = None,
        prefer_grpc: bool = False,
    ):
        """Initialize the Qdrant vector store.

        Args:
            collection_name: Name of the Qdrant collection.
            host: Qdrant server host.
            port: Qdrant server HTTP port.
            api_key: Optional API key for authenticated Qdrant instances.
            prefer_grpc: Whether to prefer gRPC over HTTP.
        """
        self.collection_name = collection_name
        self.host = host
        self.port = port
        self._client = QdrantClient(
            host=host,
            port=port,
            api_key=api_key,
            prefer_grpc=prefer_grpc,
        )

    async def create_collection(self, dimension: int) -> None:
        """Create the collection if it does not already exist.

        Args:
            dimension: Dimensionality of the vectors to store.
        """
        loop = asyncio.get_event_loop()

        collections = await loop.run_in_executor(
            None, self._client.get_collections
        )
        existing = [c.name for c in collections.collections]

        if self.collection_name in existing:
            logger.info("Collection '%s' already exists", self.collection_name)
            return

        await loop.run_in_executor(
            None,
            partial(
                self._client.create_collection,
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=dimension, distance=Distance.COSINE),
            ),
        )
        logger.info(
            "Created Qdrant collection '%s' with dimension %d",
            self.collection_name,
            dimension,
        )

    async def upsert(self, points: list[dict]) -> None:
        """Insert or update points in the collection.

        Args:
            points: List of dicts with keys 'id' (str or UUID),
                    'vector' (list[float]), and 'payload' (dict).
        """
        if not points:
            return

        qdrant_points = [
            PointStruct(
                id=str(p["id"]),
                vector=p["vector"],
                payload=p.get("payload", {}),
            )
            for p in points
        ]

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            partial(
                self._client.upsert,
                collection_name=self.collection_name,
                points=qdrant_points,
            ),
        )
        logger.debug("Upserted %d points into '%s'", len(points), self.collection_name)

    async def search(
        self,
        query_vector: list[float],
        top_k: int = 10,
        filters: dict | None = None,
    ) -> list[dict]:
        """Search for similar vectors.

        Args:
            query_vector: The query embedding vector.
            top_k: Maximum number of results to return.
            filters: Optional dict of field→value filters.

        Returns:
            List of result dicts with 'id', 'score', and 'payload' keys.
        """
        qdrant_filter = None
        if filters:
            conditions = [
                FieldCondition(key=key, match=MatchValue(value=value))
                for key, value in filters.items()
            ]
            qdrant_filter = Filter(must=conditions)

        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            partial(
                self._client.search,
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k,
                query_filter=qdrant_filter,
            ),
        )

        return [
            {
                "id": str(hit.id),
                "score": hit.score,
                "payload": hit.payload or {},
            }
            for hit in results
        ]

    async def delete_by_document(self, document_id: uuid.UUID) -> None:
        """Delete all points belonging to a specific document.

        Args:
            document_id: The document UUID whose chunks should be removed.
        """
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            partial(
                self._client.delete,
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=str(document_id)),
                        )
                    ]
                ),
            ),
        )
        logger.info(
            "Deleted chunks for document '%s' from '%s'",
            document_id,
            self.collection_name,
        )

    async def delete_collection(self) -> None:
        """Delete the entire collection."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            partial(self._client.delete_collection, collection_name=self.collection_name),
        )
        logger.info("Deleted collection '%s'", self.collection_name)

    async def collection_exists(self) -> bool:
        """Check whether the collection exists.

        Returns:
            True if the collection is present in Qdrant.
        """
        loop = asyncio.get_event_loop()
        collections = await loop.run_in_executor(None, self._client.get_collections)
        return any(c.name == self.collection_name for c in collections.collections)

    async def get_collection_info(self) -> dict:
        """Return metadata about the collection.

        Returns:
            Dict with 'vectors_count', 'points_count', etc.
        """
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(
            None,
            partial(self._client.get_collection, collection_name=self.collection_name),
        )
        return {
            "vectors_count": info.vectors_count,
            "points_count": info.points_count,
            "status": str(info.status),
        }
