"""
Base chunker abstraction.

Provides the abstract base class, Chunk dataclass, and factory
for all text chunking strategies.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    """Represents a chunk of text produced by a chunker.

    Attributes:
        content: The text content of the chunk.
        chunk_index: Position of this chunk within the document.
        token_count: Approximate token count of the content.
        chunk_type: Strategy identifier ('recursive', 'semantic', 'parent', 'child').
        metadata: Optional metadata (e.g., headings, page numbers).
    """

    content: str
    chunk_index: int
    token_count: int
    chunk_type: str
    metadata: dict | None = None


class BaseChunker(ABC):
    """Abstract base class for text chunking strategies."""

    @abstractmethod
    def chunk(self, text: str) -> list[Chunk]:
        """Split text into chunks.

        Args:
            text: The full document text to chunk.

        Returns:
            Ordered list of Chunk objects.
        """
        ...

    @staticmethod
    def create_chunker(strategy: str = "recursive", **kwargs) -> "BaseChunker":
        """Factory method to create a chunker by strategy name.

        Args:
            strategy: One of 'recursive', 'semantic', 'parent_child'.
            **kwargs: Additional arguments passed to the chunker constructor.

        Returns:
            An instantiated chunker.

        Raises:
            ValueError: If the strategy name is unknown.
        """
        from app.rag.chunking.recursive import RecursiveChunker
        from app.rag.chunking.semantic import SemanticChunker
        from app.rag.chunking.parent_child import ParentChildChunker

        strategies: dict[str, type[BaseChunker]] = {
            "recursive": RecursiveChunker,
            "semantic": SemanticChunker,
            "parent_child": ParentChildChunker,
        }

        if strategy not in strategies:
            raise ValueError(
                f"Unknown chunking strategy '{strategy}'. "
                f"Available: {list(strategies.keys())}"
            )

        chunker_cls = strategies[strategy]
        logger.debug("Created %s chunker", strategy)
        return chunker_cls(**kwargs)

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Estimate token count using a simple word-based heuristic.

        Args:
            text: Text to estimate tokens for.

        Returns:
            Estimated number of tokens.
        """
        return max(1, len(text.split()))
