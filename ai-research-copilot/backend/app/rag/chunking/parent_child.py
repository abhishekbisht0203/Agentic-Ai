"""
Parent-child chunking strategy.

Creates small child chunks for precise retrieval and large parent
chunks that provide broader context. During retrieval, child chunks
are matched, but the parent chunk is returned as context.
"""

import logging
import re

from app.rag.chunking.base import BaseChunker, Chunk

logger = logging.getLogger(__name__)

_DEFAULT_CHILD_SIZE = 200
_DEFAULT_PARENT_SIZE = 1000
_OVERLAP = 50
_SENTENCE_DELIMITERS = re.compile(r"(?<=[.!?])\s+")
_PARAGRAPH_DELIMITERS = re.compile(r"\n\s*\n")


class ParentChildChunker(BaseChunker):
    """Produce paired parent and child chunks for retrieval with context.

    Child chunks are small (default 200 tokens) for precise semantic matching.
    Parent chunks are large (default 1000 tokens) and encompass one or more
    child chunks, providing richer context when a child is retrieved.
    """

    def __init__(
        self,
        child_size: int = _DEFAULT_CHILD_SIZE,
        parent_size: int = _DEFAULT_PARENT_SIZE,
        overlap: int = _OVERLAP,
    ):
        self.child_size = child_size
        self.parent_size = parent_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[Chunk]:
        """Create parent and child chunks from text.

        Args:
            text: Full document text.

        Returns:
            List of Chunk objects. Parent chunks come first (chunk_type='parent'),
            followed by child chunks (chunk_type='child') that each carry
            metadata with their parent's chunk_index.
        """
        if not text or not text.strip():
            return []

        parent_chunks = self._create_parent_chunks(text)
        child_chunks = self._create_child_chunks(text, parent_chunks)

        all_chunks = parent_chunks + child_chunks
        logger.debug(
            "ParentChildChunker produced %d parents + %d children",
            len(parent_chunks),
            len(child_chunks),
        )
        return all_chunks

    def _create_parent_chunks(self, text: str) -> list[Chunk]:
        """Split text into large parent chunks."""
        paragraphs = _PARAGRAPH_DELIMITERS.split(text)
        merged = self._merge_to_size(paragraphs, self.parent_size)

        chunks: list[Chunk] = []
        for i, piece in enumerate(merged):
            piece = piece.strip()
            if piece:
                chunks.append(
                    Chunk(
                        content=piece,
                        chunk_index=i,
                        token_count=max(1, len(piece.split())),
                        chunk_type="parent",
                    )
                )
        return chunks

    def _create_child_chunks(self, text: str, parents: list[Chunk]) -> list[Chunk]:
        """Create small child chunks, each linked to a parent."""
        child_idx = 0
        all_children: list[Chunk] = []

        for parent in parents:
            sentences = _SENTENCE_DELIMITERS.split(parent.content)
            sentences = [s.strip() for s in sentences if s.strip()]

            child_sentences: list[str] = []
            for sentence in sentences:
                child_sentences.append(sentence)
                current_text = " ".join(child_sentences)
                if max(1, len(current_text.split())) >= self.child_size:
                    all_children.append(
                        Chunk(
                            content=current_text,
                            chunk_index=child_idx,
                            token_count=max(1, len(current_text.split())),
                            chunk_type="child",
                            metadata={"parent_chunk_index": parent.chunk_index},
                        )
                    )
                    child_idx += 1
                    child_sentences = child_sentences[-1:] if self.overlap > 0 else []

            if child_sentences:
                remaining = " ".join(child_sentences)
                if remaining.strip():
                    all_children.append(
                        Chunk(
                            content=remaining,
                            chunk_index=child_idx,
                            token_count=max(1, len(remaining.split())),
                            chunk_type="child",
                            metadata={"parent_chunk_index": parent.chunk_index},
                        )
                    )
                    child_idx += 1

        return all_children

    def _merge_to_size(self, pieces: list[str], target_size: int) -> list[str]:
        """Merge text pieces up to target_size tokens."""
        merged: list[str] = []
        buffer = ""

        for piece in pieces:
            piece = piece.strip()
            if not piece:
                continue
            candidate = f"{buffer}\n\n{piece}".strip() if buffer else piece
            if max(1, len(candidate.split())) <= target_size:
                buffer = candidate
            else:
                if buffer:
                    merged.append(buffer)
                buffer = piece

        if buffer:
            merged.append(buffer)

        return merged
