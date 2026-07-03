"""
Web page loader.

Fetches and extracts text from web URLs using httpx and BeautifulSoup4.
"""

import logging

import httpx
from bs4 import BeautifulSoup

from app.rag.loaders.base import BaseDocumentLoader

logger = logging.getLogger(__name__)

_STRIP_TAGS = {"script", "style", "meta", "link", "nav", "footer", "header"}
_DEFAULT_TIMEOUT = 30.0


class WebPageLoader(BaseDocumentLoader):
    """Load and extract text from web pages."""

    def __init__(self, timeout: float = _DEFAULT_TIMEOUT):
        self.timeout = timeout

    async def load(self, content: bytes, filename: str) -> str:
        """Extract text from HTML content (bytes form).

        This is used when content is already fetched. For URL-based
        loading, use ``load_from_url`` instead.

        Args:
            content: Raw HTML bytes.
            filename: Original filename/url for logging.

        Returns:
            Extracted plain text.
        """
        encodings = ["utf-8", "latin-1"]
        html_str = None
        for enc in encodings:
            try:
                html_str = content.decode(enc)
                break
            except (UnicodeDecodeError, LookupError):
                continue

        if html_str is None:
            raise ValueError(f"Could not decode HTML from '{filename}'")

        return self._parse_html(html_str, filename)

    async def load_from_url(self, url: str) -> str:
        """Fetch a URL and extract its text content.

        Args:
            url: The URL to fetch.

        Returns:
            Extracted plain text.

        Raises:
            ValueError: If the fetch fails or returns no text.
        """
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            try:
                response = await client.get(
                    url,
                    headers={"User-Agent": "AIResearchCopilot/1.0"},
                )
                response.raise_for_status()
            except httpx.HTTPError as exc:
                raise ValueError(f"Failed to fetch URL '{url}': {exc}") from exc

        content_type = response.headers.get("content-type", "")
        if "text/html" not in content_type and "text/plain" not in content_type:
            raise ValueError(f"URL '{url}' returned non-HTML content: {content_type}")

        html_str = response.text
        return self._parse_html(html_str, url)

    def _parse_html(self, html_str: str, source: str) -> str:
        """Parse HTML and extract visible text."""
        soup = BeautifulSoup(html_str, "html.parser")

        for tag_name in _STRIP_TAGS:
            for tag in soup.find_all(tag_name):
                tag.decompose()

        text = soup.get_text(separator="\n", strip=True)

        if not text.strip():
            raise ValueError(f"No extractable text from '{source}'")

        logger.info("Extracted text from '%s' (%d characters)", source, len(text))
        return text
