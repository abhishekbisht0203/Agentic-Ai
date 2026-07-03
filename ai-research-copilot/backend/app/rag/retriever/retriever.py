"""
Hybrid retriever combining vector search and keyword matching.

Merges results from dense (vector) retrieval and sparse (keyword)
retrieval using reciprocal rank fusion to produce a unified ranking.
"""

import logging
import re
from collections import defaultdict

from app.rag.embeddings.embedder import EmbeddingService
from app.rag.vectorstore.qdrant_store import QdrantVectorStore

logger = logging.getLogger(__name__)

_RRF_K = 60  # Constant for reciprocal rank fusion


class HybridRetriever:
    """Retrieve relevant chunks using hybrid dense + sparse search.

    Combines cosine-similarity vector search from Qdrant with a simple
    keyword-matching fallback. Results from both methods are merged
    using Reciprocal Rank Fusion (RRF).
    """

    def __init__(self, vector_store: QdrantVectorStore, embedder: EmbeddingService):
        """Initialize the hybrid retriever.

        Args:
            vector_store: The Qdrant vector store to search.
            embedder: The embedding service for query vectorization.
        """
        self.vector_store = vector_store
        self.embedder = embedder

    async def retrieve(
        self, query: str, top_k: int = 5, filters: dict | None = None
    ) -> list[dict]:
        """Retrieve relevant chunks using hybrid search.

        Args:
            query: The user query text.
            top_k: Number of final results to return.
            filters: Optional metadata filters.

        Returns:
            Ranked list of chunk dicts with 'id', 'payload', 'score' keys.
        """
        vector_results = await self._vector_search(query, top_k=top_k * 2, filters=filters)
        keyword_results = await self._keyword_search(query, top_k=top_k * 2, filters=filters)

        merged = self._rrf_merge(vector_results, keyword_results)
        return merged[:top_k]

    async def retrieve_with_scores(
        self, query: str, top_k: int = 5, filters: dict | None = None
    ) -> list[tuple[dict, float]]:
        """Retrieve chunks with their similarity scores.

        Args:
            query: The user query text.
            top_k: Number of results to return.
            filters: Optional metadata filters.

        Returns:
            List of (chunk_dict, score) tuples.
        """
        results = await self.retrieve(query, top_k=top_k, filters=filters)
        return [(r, r.get("score", 0.0)) for r in results]

    async def _vector_search(
        self, query: str, top_k: int, filters: dict | None
    ) -> list[dict]:
        """Perform dense vector search via Qdrant."""
        try:
            query_vector = await self.embedder.embed_text(query)
            results = await self.vector_store.search(
                query_vector=query_vector, top_k=top_k, filters=filters
            )
            return results
        except Exception as exc:
            logger.warning("Vector search failed: %s", exc)
            return []

    async def _keyword_search(
        self, query: str, top_k: int, filters: dict | None
    ) -> list[dict]:
        """Perform keyword-based search by embedding query tokens.

        This is a simplified approach: the query is split into meaningful
        tokens, and each token is searched separately. Results are
        de-duplicated and ranked by the number of matching tokens.
        """
        tokens = self._extract_keywords(query)
        if not tokens:
            return []

        candidate_scores: dict[str, float] = defaultdict(float)
        candidate_payloads: dict[str, dict] = {}

        for token in tokens:
            try:
                token_vector = await self.embedder.embed_text(token)
                results = await self.vector_store.search(
                    query_vector=token_vector, top_k=top_k, filters=filters
                )
                for rank, hit in enumerate(results):
                    hid = hit["id"]
                    candidate_scores[hid] += 1.0 / (_RRF_K + rank + 1)
                    candidate_payloads[hid] = hit
            except Exception as exc:
                logger.debug("Keyword search for token '%s' failed: %s", token, exc)

        ranked = sorted(candidate_scores.items(), key=lambda x: x[1], reverse=True)
        return [
            {
                **candidate_payloads[hid],
                "score": score,
            }
            for hid, score in ranked[:top_k]
        ]

    @staticmethod
    def _rrf_merge(list_a: list[dict], list_b: list[dict]) -> list[dict]:
        """Merge two ranked lists using Reciprocal Rank Fusion."""
        scores: dict[str, float] = defaultdict(float)
        items: dict[str, dict] = {}

        for rank, item in enumerate(list_a):
            key = item["id"]
            scores[key] += 1.0 / (_RRF_K + rank + 1)
            items[key] = item

        for rank, item in enumerate(list_b):
            key = item["id"]
            scores[key] += 1.0 / (_RRF_K + rank + 1)
            if key not in items:
                items[key] = item

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [
            {**items[key], "score": score}
            for key, score in ranked
        ]

    @staticmethod
    def _extract_keywords(query: str) -> list[str]:
        """Extract meaningful keywords from a query string."""
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "do", "does", "did", "will", "would", "could",
            "should", "may", "might", "shall", "can", "need", "dare", "ought",
            "used", "to", "of", "in", "for", "on", "with", "at", "by", "from",
            "as", "into", "through", "during", "before", "after", "above", "below",
            "between", "out", "off", "over", "under", "again", "further", "then",
            "once", "here", "there", "when", "where", "why", "how", "all", "both",
            "each", "few", "more", "most", "other", "some", "such", "no", "nor",
            "not", "only", "own", "same", "so", "than", "too", "very", "just",
            "don", "now", "what", "which", "who", "whom", "this", "that", "these",
            "those", "i", "me", "my", "we", "our", "you", "your", "he", "him",
            "his", "she", "her", "it", "its", "they", "them", "their",
        }
        words = re.findall(r"\b[a-z]{3,}\b", query.lower())
        return [w for w in words if w not in stop_words]
