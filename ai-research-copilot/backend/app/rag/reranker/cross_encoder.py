"""
Cross-encoder reranker.

Reranks retrieved documents using a cross-encoder model from
sentence-transformers for improved relevance ordering.
"""

import asyncio
import logging
from functools import partial

from sentence_transformers import CrossEncoder

logger = logging.getLogger(__name__)

_DEFAULT_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


class CrossEncoderReranker:
    """Rerank documents using a cross-encoder model.

    Cross-encoders jointly process the query and each document,
    producing a relevance score. This yields higher quality rankings
    than bi-encoder similarity alone.
    """

    def __init__(self, model_name: str = _DEFAULT_MODEL):
        """Initialize the reranker.

        Args:
            model_name: Name of the cross-encoder model to use.
        """
        self.model_name = model_name
        self._model: CrossEncoder | None = None

    def _get_model(self) -> CrossEncoder:
        """Lazy-load the cross-encoder model."""
        if self._model is None:
            logger.info("Loading cross-encoder model '%s'", self.model_name)
            self._model = CrossEncoder(self.model_name)
        return self._model

    async def rerank(
        self, query: str, documents: list[dict], top_k: int = 3
    ) -> list[dict]:
        """Rerank documents by cross-encoder relevance score.

        Args:
            query: The user query.
            documents: List of document dicts, each containing a 'content' or
                       'payload' with 'content' field.
            top_k: Number of top documents to return after reranking.

        Returns:
            Reranked list of document dicts with an added 'rerank_score' field.
        """
        if not documents:
            return []

        pairs = self._build_pairs(query, documents)

        model = self._get_model()
        loop = asyncio.get_event_loop()
        scores = await loop.run_in_executor(
            None, partial(model.predict, pairs, show_progress_bar=False)
        )

        scored_docs = list(zip(documents, scores))
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        reranked: list[dict] = []
        for doc, score in scored_docs[:top_k]:
            reranked.append({**doc, "rerank_score": float(score)})

        logger.debug(
            "Reranked %d documents, returning top %d", len(documents), len(reranked)
        )
        return reranked

    @staticmethod
    def _build_pairs(query: str, documents: list[dict]) -> list[tuple[str, str]]:
        """Build query-document pairs for the cross-encoder."""
        pairs: list[tuple[str, str]] = []
        for doc in documents:
            content = doc.get("content", "")
            if not content:
                payload = doc.get("payload", {})
                content = payload.get("content", "")
            pairs.append((query, content))
        return pairs
