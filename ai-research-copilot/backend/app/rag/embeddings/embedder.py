"""
Embedding service using sentence-transformers.

Provides synchronous and async-compatible methods for generating
vector embeddings for text inputs.
"""

import asyncio
import logging
from functools import partial

from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

_DEFAULT_MODEL = "all-MiniLM-L6-v2"


class EmbeddingService:
    """Generate text embeddings using a sentence-transformer model.

    The model is loaded lazily on first use and cached for the lifetime
    of the service instance.
    """

    def __init__(self, model_name: str = _DEFAULT_MODEL):
        """Initialize the embedding service.

        Args:
            model_name: Name of the sentence-transformers model to use.
        """
        self.model_name = model_name
        self._model: SentenceTransformer | None = None

    def _get_model(self) -> SentenceTransformer:
        """Lazy-load the sentence-transformer model."""
        if self._model is None:
            logger.info("Loading embedding model '%s'", self.model_name)
            self._model = SentenceTransformer(self.model_name)
        return self._model

    async def embed_text(self, text: str) -> list[float]:
        """Generate an embedding vector for a single text.

        Args:
            text: The input text to embed.

        Returns:
            List of floats representing the embedding vector.
        """
        model = self._get_model()
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None, partial(model.encode, [text], convert_to_numpy=True, show_progress_bar=False)
        )
        return embedding[0].tolist()

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embedding vectors for a batch of texts.

        Args:
            texts: List of input texts to embed.

        Returns:
            List of embedding vectors, one per input text.
        """
        if not texts:
            return []

        model = self._get_model()
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None,
            partial(model.encode, texts, convert_to_numpy=True, show_progress_bar=False),
        )
        return [vec.tolist() for vec in embeddings]

    def get_dimension(self) -> int:
        """Return the dimension of the embedding vectors.

        Returns:
            Dimensionality of the model's output vectors.
        """
        model = self._get_model()
        return model.get_sentence_embedding_dimension()
