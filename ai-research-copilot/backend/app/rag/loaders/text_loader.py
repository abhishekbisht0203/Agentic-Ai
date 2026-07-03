"""
Plain text document loader.

Handles .txt, .md, and other plain text file formats.
"""

import logging

from app.rag.loaders.base import BaseDocumentLoader

logger = logging.getLogger(__name__)


class TextLoader(BaseDocumentLoader):
    """Load and extract text from plain text files."""

    async def load(self, content: bytes, filename: str) -> str:
        """Decode and return plain text content.

        Args:
            content: Raw file bytes.
            filename: Original filename for logging.

        Returns:
            Decoded text content.

        Raises:
            ValueError: If the content is empty or cannot be decoded.
        """
        encodings = ["utf-8", "latin-1", "ascii", "cp1252"]
        text = None

        for encoding in encodings:
            try:
                text = content.decode(encoding)
                break
            except (UnicodeDecodeError, LookupError):
                continue

        if text is None:
            raise ValueError(f"Could not decode '{filename}' with any supported encoding")

        text = text.strip()

        if not text:
            raise ValueError(f"File '{filename}' contains no text content")

        logger.info("Loaded text from '%s' (%d characters)", filename, len(text))
        return text
