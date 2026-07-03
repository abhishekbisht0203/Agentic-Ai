"""
HTML document loader.

Extracts text content from HTML files using BeautifulSoup4.
"""

import logging

from bs4 import BeautifulSoup

from app.rag.loaders.base import BaseDocumentLoader

logger = logging.getLogger(__name__)

_STRIP_TAGS = {"script", "style", "meta", "link", "head"}


class HTMLLoader(BaseDocumentLoader):
    """Load and extract text from HTML documents."""

    async def load(self, content: bytes, filename: str) -> str:
        """Extract visible text from an HTML file.

        Removes script/style elements, strips tags, and normalizes whitespace.

        Args:
            content: Raw HTML bytes.
            filename: Original filename for logging.

        Returns:
            Extracted plain text.

        Raises:
            ValueError: If no text content can be extracted.
        """
        encodings = ["utf-8", "latin-1", "ascii"]
        html_str = None

        for encoding in encodings:
            try:
                html_str = content.decode(encoding)
                break
            except (UnicodeDecodeError, LookupError):
                continue

        if html_str is None:
            raise ValueError(f"Could not decode HTML from '{filename}'")

        soup = BeautifulSoup(html_str, "html.parser")

        for tag_name in _STRIP_TAGS:
            for tag in soup.find_all(tag_name):
                tag.decompose()

        text = soup.get_text(separator="\n", strip=True)

        if not text.strip():
            raise ValueError(f"HTML '{filename}' contains no extractable text")

        logger.info("Extracted text from HTML '%s' (%d characters)", filename, len(text))
        return text
