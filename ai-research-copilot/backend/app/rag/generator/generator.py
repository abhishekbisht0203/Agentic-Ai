"""
RAG response generator.

Combines retrieval, reranking, and LLM generation to produce
grounded responses with citations.
"""

import logging
from typing import Any, AsyncIterator

from app.rag.citation.citations import CitationGenerator
from app.rag.reranker.cross_encoder import CrossEncoderReranker
from app.rag.retriever.retriever import HybridRetriever

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are ARC, the AI Research Copilot. Answer the user's question
using ONLY the provided context. If the context does not contain enough information
to answer the question, say so explicitly. Always cite your sources using [1], [2],
etc. notation when referencing specific pieces of context."""

_CONTEXT_TEMPLATE = """Context information:
{context}

Question: {query}

Please provide a comprehensive answer based on the context above. Cite sources using [1], [2] notation."""


class RAGGenerator:
    """Generate responses using Retrieval-Augmented Generation.

    Orchestrates the full RAG flow: retrieve relevant chunks, rerank
    them for relevance, build a context prompt, and call the LLM.
    """

    def __init__(
        self,
        llm_provider: Any,
        retriever: HybridRetriever,
        reranker: CrossEncoderReranker,
    ):
        """Initialize the RAG generator.

        Args:
            llm_provider: An LLM provider with an async ``generate`` or ``chat``
                           method accepting messages.
            retriever: The hybrid retriever for document search.
            reranker: The cross-encoder reranker for re-ordering.
        """
        self.llm_provider = llm_provider
        self.retriever = retriever
        self.reranker = reranker

    async def generate(
        self, query: str, top_k: int = 5, stream: bool = False
    ) -> dict:
        """Generate a RAG response for the given query.

        Args:
            query: The user's question.
            top_k: Number of chunks to retrieve and rerank.
            stream: Whether to stream the response (not yet supported).

        Returns:
            Dict with 'response' (str) and 'citations' (list[dict]) keys.
        """
        logger.info("RAG generate: query='%s', top_k=%d", query[:80], top_k)

        retrieved = await self.retriever.retrieve(query, top_k=top_k)
        if not retrieved:
            logger.warning("No documents retrieved for query")
            return {
                "response": "I could not find any relevant documents to answer your question.",
                "citations": [],
                "retrieved_chunks": [],
            }

        reranked = await self.reranker.rerank(query, retrieved, top_k=min(3, len(retrieved)))

        context = self._build_context(reranked)
        prompt = _CONTEXT_TEMPLATE.format(context=context, query=query)

        response_text = await self._call_llm(prompt)

        citations = CitationGenerator.generate_citations(reranked, response_text)

        return {
            "response": response_text,
            "citations": citations,
            "retrieved_chunks": reranked,
        }

    async def generate_stream(
        self, query: str, top_k: int = 5
    ) -> AsyncIterator[str]:
        """Generate a streaming RAG response.

        Yields response chunks as they become available from the LLM.

        Args:
            query: The user's question.
            top_k: Number of chunks to retrieve.

        Yields:
            String fragments of the response.
        """
        retrieved = await self.retriever.retrieve(query, top_k=top_k)
        if not retrieved:
            yield "I could not find any relevant documents to answer your question."
            return

        reranked = await self.reranker.rerank(query, retrieved, top_k=min(3, len(retrieved)))
        context = self._build_context(reranked)
        prompt = _CONTEXT_TEMPLATE.format(context=context, query=query)

        if hasattr(self.llm_provider, "generate_stream"):
            async for chunk in self.llm_provider.generate_stream(
                prompt, system_prompt=_SYSTEM_PROMPT
            ):
                yield chunk
        else:
            response = await self._call_llm(prompt)
            yield response

    def _build_context(self, chunks: list[dict]) -> str:
        """Build context string from retrieved chunks."""
        parts: list[str] = []
        for i, chunk in enumerate(chunks, 1):
            payload = chunk.get("payload", chunk)
            content = payload.get("content", "")
            doc_id = payload.get("document_id", "unknown")
            parts.append(f"[{i}] (Document: {doc_id})\n{content}")
        return "\n\n".join(parts)

    async def _call_llm(self, prompt: str) -> str:
        """Call the LLM provider with the constructed prompt."""
        try:
            if hasattr(self.llm_provider, "generate"):
                result = await self.llm_provider.generate(
                    prompt, system_prompt=_SYSTEM_PROMPT
                )
                return result
            elif hasattr(self.llm_provider, "chat"):
                messages = [
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ]
                result = await self.llm_provider.chat(messages)
                return result
            else:
                raise AttributeError(
                    "LLM provider must have 'generate' or 'chat' method"
                )
        except Exception as exc:
            logger.error("LLM call failed: %s", exc)
            return (
                "I encountered an error while generating a response. "
                "Please try again later."
            )
