"""
YouTube transcript loader.

Fetches and extracts transcripts from YouTube videos using youtube_transcript_api.
"""

import logging
import re

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter

from app.rag.loaders.base import BaseDocumentLoader

logger = logging.getLogger(__name__)

_YOUTUBE_URL_PATTERN = re.compile(
    r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})"
)


class YouTubeLoader(BaseDocumentLoader):
    """Load transcripts from YouTube videos."""

    async def load(self, content: bytes, filename: str) -> str:
        """Load transcript from content treated as a URL string.

        Args:
            content: URL bytes for the YouTube video.
            filename: Original filename/url for logging.

        Returns:
            Formatted transcript text.

        Raises:
            ValueError: If no video ID can be extracted or transcript unavailable.
        """
        url = content.decode("utf-8").strip()
        video_id = self._extract_video_id(url)
        if not video_id:
            raise ValueError(f"Could not extract video ID from '{filename}'")
        return await self._fetch_transcript(video_id, filename)

    async def load_from_url(self, url: str) -> str:
        """Fetch transcript directly from a YouTube URL.

        Args:
            url: YouTube video URL.

        Returns:
            Formatted transcript text.

        Raises:
            ValueError: If video ID cannot be extracted or transcript unavailable.
        """
        video_id = self._extract_video_id(url)
        if not video_id:
            raise ValueError(f"Could not extract video ID from URL: {url}")
        return await self._fetch_transcript(video_id, url)

    @staticmethod
    def _extract_video_id(url: str) -> str | None:
        """Extract the 11-character video ID from a YouTube URL."""
        match = _YOUTUBE_URL_PATTERN.search(url)
        if match:
            return match.group(1)
        clean = url.strip()
        if re.fullmatch(r"[a-zA-Z0-9_-]{11}", clean):
            return clean
        return None

    @staticmethod
    async def _fetch_transcript(video_id: str, source: str) -> str:
        """Fetch and format the transcript for a given video ID."""
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        except Exception as exc:
            raise ValueError(
                f"Failed to fetch transcript for video '{video_id}' from '{source}': {exc}"
            ) from exc

        formatter = TextFormatter()
        text = formatter.format_transcript(transcript_list)

        if not text.strip():
            raise ValueError(f"Transcript for video '{video_id}' is empty")

        logger.info(
            "Fetched transcript for video '%s' (%d segments)", video_id, len(transcript_list)
        )
        return text
