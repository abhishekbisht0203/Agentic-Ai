"""
Recursive text splitter chunking.

Splits text hierarchically: first by paragraphs, then sentences,
then words, to produce chunks of roughly the desired size.
"""

import logging
import re

from app.rag.chunking.base import BaseChunker, Chunk

logger = logging.getLogger(__name__)

_DEFAULT_CHUNK_SIZE = 512
_DEFAULT_CHUNK_OVERLAP = 50
_SENTENCE_DELIMITERS = re.compile(r"(?<=[.!?])\s+")
_PARAGRAPH_DELIMITERS = re.compile(r"\n\s*\n")


class RecursiveChunker(BaseChunker):
    """Chunk text by recursively splitting at decreasing granularity levels.

    Strategy:
    1. Split by double-newline paragraphs.
    2. If a paragraph is too large, split by sentence delimiters.
    3. If a sentence is still too large, split by word boundaries.
    4. Merge small consecutive pieces up to the chunk size limit.
    """

    def __init__(
        self,
        chunk_size: int = _DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = _DEFAULT_CHUNK_OVERLAP,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, text: str) -> list[Chunk]:
        """Split text into recursively-sized chunks.

        Args:
            text: Full document text.

        Returns:
            List of Chunk objects.
        """
        if not text or not text.strip():
            return []

        paragraphs = _PARAGRAPH_DELIMITERS.split(text)
        raw_pieces: list[str] = []

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            if self._token_count(para) <= self.chunk_size:
                raw_pieces.append(para)
            else:
                raw_pieces.extend(self._split_sentences(para))

        merged = self._merge_pieces(raw_pieces)

        chunks = [
            Chunk(
                content=piece.strip(),
                chunk_index=i,
                token_count=self._token_count(piece.strip()),
                chunk_type="recursive",
            )
            for i, piece in enumerate(merged)
            if piece.strip()
        ]

        logger.debug("RecursiveChunker produced %d chunks", len(chunks))
        return chunks

    def _split_sentences(self, text: str) -> list[str]:
        """Split text into sentences, then words if needed."""
        sentences = _SENTENCE_DELIMITERS.split(text)
        pieces: list[str] = []

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            if self._token_count(sentence) <= self.chunk_size:
                pieces.append(sentence)
            else:
                pieces.extend(self._split_words(sentence))

        return pieces

    def _split_words(self, text: str) -> list[str]:
        """Split text into word-level chunks."""
        words = text.split()
        pieces: list[str] = []
        current: list[str] = []

        for word in words:
            current.append(word)
            if len(current) >= self.chunk_size - self.chunk_overlap:
                pieces.append(" ".join(current))
                current = current[-self.chunk_overlap:] if self.chunk_overlap else []

        if current:
            pieces.append(" ".join(current))

        return pieces

    def _merge_pieces(self, pieces: list[str]) -> list[str]:
        """Merge small consecutive pieces to fill chunk_size."""
        if not pieces:
            return []

        merged: list[str] = []
        buffer = ""

        for piece in pieces:
            candidate = f"{buffer}\n\n{piece}".strip() if buffer else piece
            if self._token_count(candidate) <= self.chunk_size:
                buffer = candidate
            else:
                if buffer:
                    merged.append(buffer)
                buffer = piece

        if buffer:
            merged.append(buffer)

        return merged

    def _token_count(self, text: str) -> int:
        return max(1, len(text.split()))
