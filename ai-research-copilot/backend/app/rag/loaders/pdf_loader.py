"""
PDF document loader.

Extracts text from PDF files page-by-page using PyPDF2.
"""

import logging
from io import BytesIO

from PyPDF2 import PdfReader

from app.rag.loaders.base import BaseDocumentLoader

logger = logging.getLogger(__name__)


class PDFLoader(BaseDocumentLoader):
    """Load and extract text from PDF documents."""

    async def load(self, content: bytes, filename: str) -> str:
        """Extract text from a PDF file.

        Args:
            content: Raw PDF bytes.
            filename: Original filename for logging.

        Returns:
            Extracted text with pages separated by double newlines.

        Raises:
            ValueError: If the PDF cannot be parsed.
        """
        try:
            reader = PdfReader(BytesIO(content))
        except Exception as exc:
            raise ValueError(f"Failed to parse PDF '{filename}': {exc}") from exc

        pages: list[str] = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                pages.append(text.strip())
            else:
                logger.warning("Page %d of '%s' yielded no text", i + 1, filename)

        full_text = "\n\n".join(pages)

        if not full_text.strip():
            raise ValueError(f"PDF '{filename}' contains no extractable text")

        logger.info("Extracted %d pages from '%s'", len(pages), filename)
        return full_text
