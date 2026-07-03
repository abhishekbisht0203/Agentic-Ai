"""
Chunking package.

Provides various text chunking strategies for the RAG pipeline.
"""

from app.rag.chunking.base import BaseChunker, Chunk

__all__ = ["BaseChunker", "Chunk"]
