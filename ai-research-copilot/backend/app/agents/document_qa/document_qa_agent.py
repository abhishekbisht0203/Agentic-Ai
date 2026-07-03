"""
Document Q&A agent – answers questions about documents using RAG.
"""

import json
import uuid
import logging
from typing import Any

from app.agents.base.agent import BaseAgent
from app.llms.providers.base import BaseLLMProvider
from app.llms.prompts.templates import DOCUMENT_QA_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class DocumentQAAgent(BaseAgent):
    """Answers user questions grounded in document context via RAG.

    Workflow:
    1. Retrieve relevant chunks from the vector store.
    2. Assemble a context prompt with citations.
    3. Generate an answer with confidence scoring.
    """

    agent_type: str = "document_qa"

    def __init__(self, llm_provider: BaseLLMProvider, config: dict[str, Any] | None = None) -> None:
        super().__init__(llm_provider, config)
        self._rag_pipeline: Any = None

    def set_rag_pipeline(self, rag_pipeline: Any) -> None:
        """Inject a RAG pipeline instance for document retrieval."""
        self._rag_pipeline = rag_pipeline

    # ------------------------------------------------------------------
    # Core interface
    # ------------------------------------------------------------------

    async def execute(
        self,
        input_data: dict[str, Any],
        conversation_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        """Answer a question using document context.

        Parameters
        ----------
        input_data : dict
            ``"message"``: the user's question.
            ``"knowledge_base_id"`` (optional): scope retrieval to a specific KB.
            ``"rag_context"`` (optional): pre-retrieved context (bypass RAG).
            ``"filters"`` (optional): metadata filters for retrieval.

        Returns
        -------
        dict
            ``{"answer": …, "sources": …, "confidence": …,
            "follow_up_questions": …, "context_used": …}``
        """
        message = input_data.get("message", "")
        if not message:
            return {
                "answer": "",
                "sources": [],
                "confidence": "low",
                "follow_up_questions": [],
                "context_used": "",
                "error": "No question provided.",
            }

        self.logger.info("Document QA processing: %r", message[:120])
        self.memory.add("user", message)

        kb_id = input_data.get("knowledge_base_id")
        filters = input_data.get("filters")
        rag_context = input_data.get("rag_context", "")

        # Step 1 – retrieve relevant context
        if not rag_context:
            rag_context = await self._retrieve_context(message, kb_id, filters)

        # Step 2 – answer the question
        result = await self._answer_question(message, rag_context, kb_id)

        # Step 3 – generate follow-up questions
        follow_ups = await self._suggest_follow_ups(message, result.get("answer", ""), rag_context)
        result["follow_up_questions"] = follow_ups

        self.memory.add("assistant", json.dumps(result, default=str))
        return result

    # ------------------------------------------------------------------
    # Internal steps
    # ------------------------------------------------------------------

    async def _retrieve_context(
        self,
        query: str,
        knowledge_base_id: str | None,
        filters: dict[str, Any] | None,
    ) -> str:
        """Retrieve relevant document chunks via the RAG pipeline."""
        if self._rag_pipeline is None:
            self.logger.warning("No RAG pipeline configured – answering without context")
            return ""

        try:
            result = await self._rag_pipeline.retrieve(
                query=query,
                knowledge_base_id=knowledge_base_id,
                filters=filters,
            )
            return result.context
        except Exception:
            self.logger.exception("RAG retrieval failed")
            return ""

    async def _answer_question(
        self, question: str, context: str, knowledge_base_id: str | None
    ) -> dict[str, Any]:
        """Generate an answer grounded in the retrieved context."""
        if context:
            prompt = (
                f"Answer the following question using ONLY the provided context. "
                f"Cite specific passages where possible.\n\n"
                f"Context:\n{context[:6000]}\n\n"
                f"Question: {question}\n\n"
                "Respond with a JSON object:\n"
                '{"answer": "...", "sources": [{"passage": "...", "source": "..."}], '
                '"confidence": "high|medium|low"}'
            )
        else:
            prompt = (
                f"Question: {question}\n\n"
                "No document context is available. Answer based on general knowledge "
                "and clearly state that no documents were found.\n\n"
                "Respond with a JSON object:\n"
                '{"answer": "...", "sources": [], "confidence": "low"}'
            )

        messages = self._build_messages(DOCUMENT_QA_SYSTEM_PROMPT, prompt)
        try:
            response = await self._generate_response(messages, temperature=0.3, max_tokens=2000)
            parsed = self._parse_json_response(response)
            if isinstance(parsed, dict):
                parsed.setdefault("answer", "")
                parsed.setdefault("sources", [])
                parsed.setdefault("confidence", "medium")
                parsed["context_used"] = context[:2000] if context else ""
                return parsed
        except Exception:
            self.logger.exception("Answer generation failed")

        return {
            "answer": "Unable to generate an answer.",
            "sources": [],
            "confidence": "low",
            "context_used": context[:2000] if context else "",
        }

    async def _suggest_follow_ups(
        self, question: str, answer: str, context: str
    ) -> list[str]:
        """Suggest relevant follow-up questions."""
        if not context:
            return []

        prompt = (
            f"Based on the following Q&A exchange, suggest 2-4 relevant follow-up "
            f"questions the user might want to ask.\n\n"
            f"Original question: {question}\n"
            f"Answer: {answer[:1000]}\n"
            f"Available context: {context[:2000]}\n\n"
            "Return ONLY a JSON array of question strings."
        )

        messages = self._build_messages(DOCUMENT_QA_SYSTEM_PROMPT, prompt)
        try:
            response = await self._generate_response(messages, temperature=0.5, max_tokens=500)
            parsed = self._parse_json_response(response)
            if isinstance(parsed, list):
                return [str(q) for q in parsed]
            if isinstance(parsed, dict) and "follow_up_questions" in parsed:
                return [str(q) for q in parsed["follow_up_questions"]]
        except Exception:
            self.logger.warning("Follow-up suggestion failed")

        return []
