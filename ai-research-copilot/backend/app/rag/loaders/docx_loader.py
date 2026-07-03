"""
DOCX document loader.

Extracts text from Microsoft Word (.docx) files using python-docx.
"""

import logging
from io import BytesIO

from docx import Document as DocxDocument

from app.rag.loaders.base import BaseDocumentLoader

logger = logging.getLogger(__name__)


class DOCXLoader(BaseDocumentLoader):
    """Load and extract text from DOCX documents."""

    async def load(self, content: bytes, filename: str) -> str:
        """Extract text from a DOCX file.

        Args:
            content: Raw DOCX bytes.
            filename: Original filename for logging.

        Returns:
            Extracted text with paragraphs separated by newlines.

        Raises:
            ValueError: If the DOCX cannot be parsed.
        """
        try:
            doc = DocxDocument(BytesIO(content))
        except Exception as exc:
            raise ValueError(f"Failed to parse DOCX '{filename}': {exc}") from exc

        paragraphs: list[str] = []
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                paragraphs.append(text)

        full_text = "\n\n".join(paragraphs)

        if not full_text.strip():
            raise ValueError(f"DOCX '{filename}' contains no extractable text")

        logger.info("Extracted %d paragraphs from '%s'", len(paragraphs), filename)
        return full_text
