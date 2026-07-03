"""
Citation generation utilities.

Produces structured citation objects from retrieved chunks and
formats them for inclusion in generated responses.
"""

import logging

logger = logging.getLogger(__name__)


class CitationGenerator:
    """Generate and format citations from retrieved document chunks."""

    @staticmethod
    def generate_citations(retrieved_chunks: list[dict], response: str) -> list[dict]:
        """Generate citations from retrieved chunks.

        Each chunk that appears to be referenced in the response text
        is included as a citation. A chunk is considered referenced if
        at least 5 significant words from the chunk appear in the response.

        Args:
            retrieved_chunks: List of chunk dicts with 'payload' containing
                              'content', 'document_id', 'chunk_index', etc.
            response: The generated response text.

        Returns:
            List of citation dicts with 'index', 'document_id', 'chunk_index',
            'content_preview', and 'relevance_score' keys.
        """
        if not retrieved_chunks or not response:
            return []

        response_lower = response.lower()
        response_words = set(response_lower.split())

        citations: list[dict] = []
        for i, chunk in enumerate(retrieved_chunks):
            payload = chunk.get("payload", chunk)
            content = payload.get("content", "")

            if not content:
                continue

            content_words = set(content.lower().split())
            significant_words = {w for w in content_words if len(w) > 3}
            overlap = significant_words & response_words

            if len(overlap) >= 3:
                relevance = min(1.0, len(overlap) / max(1, len(significant_words)))
                citation = CitationGenerator.format_citation(chunk, i)
                citation["relevance_score"] = relevance
                citations.append(citation)

        citations.sort(key=lambda c: c.get("relevance_score", 0), reverse=True)
        logger.debug("Generated %d citations from %d chunks", len(citations), len(retrieved_chunks))
        return citations

    @staticmethod
    def format_citation(chunk: dict, index: int) -> dict:
        """Format a single citation from a retrieved chunk.

        Args:
            chunk: The chunk dict from retrieval.
            index: The citation number (1-based in display).

        Returns:
            Structured citation dict.
        """
        payload = chunk.get("payload", chunk)
        content = payload.get("content", "")
        preview = content[:200].strip() + ("..." if len(content) > 200 else "")

        return {
            "index": index + 1,
            "document_id": payload.get("document_id", "unknown"),
            "knowledge_base_id": payload.get("knowledge_base_id", "unknown"),
            "chunk_index": payload.get("chunk_index", 0),
            "content_preview": preview,
            "chunk_type": payload.get("chunk_type", "unknown"),
            "score": chunk.get("score", 0.0),
        }

    @staticmethod
    def citations_to_text(citations: list[dict]) -> str:
        """Format citations as a human-readable string.

        Args:
            citations: List of citation dicts from generate_citations.

        Returns:
            Formatted citation text block.
        """
        if not citations:
            return ""

        lines = ["**Sources:**\n"]
        for cite in citations:
            lines.append(
                f"[{cite['index']}] {cite.get('document_id', 'Unknown')} "
                f"(chunk {cite.get('chunk_index', 0)}, "
                f"relevance: {cite.get('relevance_score', 0):.1%})"
            )
            preview = cite.get("content_preview", "")
            if preview:
                lines.append(f"    {preview}")
            lines.append("")

        return "\n".join(lines)
