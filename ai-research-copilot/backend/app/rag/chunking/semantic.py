"""
Semantic chunking.

Uses sentence-transformers embeddings to find natural break points
in text by measuring semantic similarity between consecutive sentences.
When similarity drops below a threshold, a new chunk is started.
"""

import logging
import re

import numpy as np
from sentence_transformers import SentenceTransformer

from app.rag.chunking.base import BaseChunker, Chunk

logger = logging.getLogger(__name__)

_DEFAULT_MODEL = "all-MiniLM-L6-v2"
_DEFAULT_CHUNK_SIZE = 512
_SIMILARITY_THRESHOLD = 0.5
_SENTENCE_SPLITTER = re.compile(r"(?<=[.!?])\s+")


class SemanticChunker(BaseChunker):
    """Chunk text based on semantic similarity between sentences.

    Uses a sentence-transformer model to compute embeddings for each
    sentence, then identifies break points where cosine similarity
    between adjacent sentences drops below a threshold.
    """

    def __init__(
        self,
        model_name: str = _DEFAULT_MODEL,
        chunk_size: int = _DEFAULT_CHUNK_SIZE,
        similarity_threshold: float = _SIMILARITY_THRESHOLD,
    ):
        self.model_name = model_name
        self.chunk_size = chunk_size
        self.similarity_threshold = similarity_threshold
        self._model: SentenceTransformer | None = None

    def _get_model(self) -> SentenceTransformer:
        """Lazy-load the sentence-transformer model."""
        if self._model is None:
            logger.info("Loading semantic chunking model '%s'", self.model_name)
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def chunk(self, text: str) -> list[Chunk]:
        """Split text into semantically coherent chunks.

        Args:
            text: Full document text.

        Returns:
            List of Chunk objects with type 'semantic'.
        """
        if not text or not text.strip():
            return []

        sentences = _SENTENCE_SPLITTER.split(text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if len(sentences) <= 2:
            return [
                Chunk(
                    content=text.strip(),
                    chunk_index=0,
                    token_count=max(1, len(text.split())),
                    chunk_type="semantic",
                )
            ]

        model = self._get_model()
        embeddings = model.encode(sentences, convert_to_numpy=True, show_progress_bar=False)

        similarities = self._compute_similarities(embeddings)
        break_points = self._find_break_points(similarities)

        chunks = self._build_chunks_from_breakpoints(sentences, break_points)

        logger.debug("SemanticChunker produced %d chunks from %d sentences", len(chunks), len(sentences))
        return chunks

    @staticmethod
    def _compute_similarities(embeddings: np.ndarray) -> list[float]:
        """Compute cosine similarity between consecutive sentence embeddings."""
        similarities: list[float] = []
        for i in range(len(embeddings) - 1):
            dot = np.dot(embeddings[i], embeddings[i + 1])
            norm = np.linalg.norm(embeddings[i]) * np.linalg.norm(embeddings[i + 1])
            sim = float(dot / norm) if norm > 0 else 0.0
            similarities.append(sim)
        return similarities

    def _find_break_points(self, similarities: list[float]) -> list[int]:
        """Find indices where similarity drops below the threshold."""
        breaks: list[int] = [0]
        for i, sim in enumerate(similarities):
            if sim < self.similarity_threshold:
                breaks.append(i + 1)
        return breaks

    def _build_chunks_from_breakpoints(
        self, sentences: list[str], break_points: list[int]
    ) -> list[Chunk]:
        """Build chunks from identified break points, respecting chunk_size."""
        chunks: list[Chunk] = []
        chunk_idx = 0

        for bp_idx, start in enumerate(break_points):
            end = break_points[bp_idx + 1] if bp_idx + 1 < len(break_points) else len(sentences)
            segment = " ".join(sentences[start:end])

            if max(1, len(segment.split())) <= self.chunk_size:
                chunks.append(
                    Chunk(
                        content=segment,
                        chunk_index=chunk_idx,
                        token_count=max(1, len(segment.split())),
                        chunk_type="semantic",
                        metadata={"sentence_range": [start, end - 1]},
                    )
                )
                chunk_idx += 1
            else:
                words = segment.split()
                for i in range(0, len(words), self.chunk_size):
                    piece = " ".join(words[i : i + self.chunk_size])
                    chunks.append(
                        Chunk(
                            content=piece,
                            chunk_index=chunk_idx,
                            token_count=max(1, len(piece.split())),
                            chunk_type="semantic",
                            metadata={"sentence_range": [start, end - 1]},
                        )
                    )
                    chunk_idx += 1

        return chunks
