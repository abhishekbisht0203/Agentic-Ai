"""
Research agent – gathers and synthesises information on a given topic.

The agent decomposes a query into sub-questions, synthesises findings from
available knowledge, and produces a structured report.
"""

import json
import uuid
import logging
from typing import Any

from app.agents.base.agent import BaseAgent
from app.llms.providers.base import BaseLLMProvider, LLMResponse
from app.llms.prompts.templates import RESEARCH_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class ResearchAgent(BaseAgent):
    """Conducts research on a topic using the LLM and optional RAG context.

    Workflow:
    1. Break the query into sub-questions.
    2. For each sub-question, gather what the LLM knows (and any RAG context).
    3. Synthesize everything into a coherent report.
    """

    agent_type: str = "research"

    def __init__(self, llm_provider: BaseLLMProvider, config: dict[str, Any] | None = None) -> None:
        super().__init__(llm_provider, config)

    # ------------------------------------------------------------------
    # Core interface
    # ------------------------------------------------------------------

    async def execute(
        self,
        input_data: dict[str, Any],
        conversation_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        """Conduct research on the topic described in ``input_data["message"]``.

        Parameters
        ----------
        input_data : dict
            ``"message"``: the research question.
            ``"rag_context"`` (optional): pre-retrieved context from documents.
            ``"depth"`` (optional): ``"shallow"`` | ``"standard"`` | ``"deep"``.

        Returns
        -------
        dict
            ``{"summary": …, "findings": …, "sources": …, "open_questions": …}``
        """
        message = input_data.get("message", "")
        if not message:
            return {"summary": "", "findings": [], "sources": [], "open_questions": [], "error": "No message provided."}

        self.logger.info("Research agent processing: %r", message[:120])
        self.memory.add("user", message)

        rag_context = input_data.get("rag_context", "")
        depth = input_data.get("depth", "standard")

        # Step 1 – decompose into sub-questions
        sub_questions = await self._decompose_query(message, rag_context)

        # Step 2 – gather findings for each sub-question
        findings: list[dict[str, Any]] = []
        for sq in sub_questions:
            finding = await self._search_information(sq, rag_context)
            findings.append(finding)

        # Step 3 – synthesize into a report
        report_text = await self._synthesize_findings(message, findings)

        # Step 4 – extract structured output
        result = await self._extract_structured_report(report_text, findings, message)

        self.memory.add("assistant", json.dumps(result, default=str))
        return result

    # ------------------------------------------------------------------
    # Sub-steps
    # ------------------------------------------------------------------

    async def _decompose_query(
        self, query: str, rag_context: str
    ) -> list[str]:
        """Break a research query into 2-5 sub-questions."""
        prompt = (
            "Break the following research query into 2 to 5 specific "
            "sub-questions that need to be answered to provide a comprehensive "
            "response.  Return ONLY a JSON array of strings.\n\n"
            f"Query: {query}"
        )
        if rag_context:
            prompt += f"\n\nAvailable context:\n{rag_context[:3000]}"

        messages = self._build_messages(RESEARCH_SYSTEM_PROMPT, prompt)
        try:
            response = await self._generate_response(messages, temperature=0.3, max_tokens=512)
            parsed = self._parse_json_response(response)
            if isinstance(parsed, list):
                return [str(s) for s in parsed]
            if isinstance(parsed, dict) and "raw" in parsed:
                # Try to find a list inside the raw text
                import re
                match = re.search(r"\[.*\]", parsed["raw"], re.DOTALL)
                if match:
                    return json.loads(match.group())
            # Fallback: return the original query
            return [query]
        except Exception:
            self.logger.warning("Query decomposition failed, using original query")
            return [query]

    async def _search_information(
        self, sub_question: str, rag_context: str
    ) -> dict[str, Any]:
        """Gather information for a single sub-question."""
        prompt = (
            f"Answer the following research question thoroughly.\n\n"
            f"Question: {sub_question}\n"
        )
        if rag_context:
            prompt += f"\nRelevant document context:\n{rag_context[:3000]}\n"
        prompt += (
            "\nProvide your findings as a JSON object with:\n"
            '{"question": "...", "answer": "...", '
            '"confidence": "high|medium|low", "key_points": ["..."]}'
        )

        messages = self._build_messages(RESEARCH_SYSTEM_PROMPT, prompt)
        try:
            response = await self._generate_response(messages, temperature=0.4, max_tokens=1500)
            parsed = self._parse_json_response(response)
            if isinstance(parsed, dict):
                parsed.setdefault("question", sub_question)
                return parsed
            return {
                "question": sub_question,
                "answer": response.content,
                "confidence": "medium",
                "key_points": [],
            }
        except Exception:
            self.logger.exception("Information search failed for: %s", sub_question[:80])
            return {
                "question": sub_question,
                "answer": "Unable to retrieve information.",
                "confidence": "low",
                "key_points": [],
            }

    async def _synthesize_findings(
        self, query: str, findings: list[dict[str, Any]]
    ) -> str:
        """Synthesize all findings into a coherent narrative."""
        findings_text = "\n\n".join(
            f"**Q:** {f.get('question', '')}\n"
            f"**A:** {f.get('answer', '')}\n"
            f"**Confidence:** {f.get('confidence', 'medium')}"
            for f in findings
        )

        prompt = (
            f"Original query: {query}\n\n"
            f"Research findings:\n{findings_text}\n\n"
            "Synthesise these findings into a clear, well-structured report. "
            "Include an executive summary, detailed findings, and any open questions."
        )

        messages = self._build_messages(RESEARCH_SYSTEM_PROMPT, prompt)
        response = await self._generate_response(messages, temperature=0.5, max_tokens=3000)
        return response.content

    async def _extract_structured_report(
        self,
        report_text: str,
        findings: list[dict[str, Any]],
        original_query: str,
    ) -> dict[str, Any]:
        """Ask the LLM to extract a structured report from the narrative."""
        prompt = (
            "Given the following research report and findings, extract a "
            "structured JSON response.\n\n"
            f"Report:\n{report_text[:4000]}\n\n"
            "Respond with:\n"
            '{"summary": "<executive summary>", "findings": [<list of strings>], '
            '"sources": [<list of source references>], '
            '"open_questions": [<list of unresolved items>]}'
        )

        messages = self._build_messages(RESEARCH_SYSTEM_PROMPT, prompt)
        try:
            response = await self._generate_response(messages, temperature=0.2, max_tokens=2000)
            parsed = self._parse_json_response(response)
            if isinstance(parsed, dict):
                parsed.setdefault("summary", report_text[:500])
                parsed.setdefault("findings", [f.get("answer", "") for f in findings])
                parsed.setdefault("sources", [])
                parsed.setdefault("open_questions", [])
                return parsed
        except Exception:
            self.logger.warning("Structured extraction failed, building manually")

        return {
            "summary": report_text[:1000],
            "findings": [f.get("answer", "") for f in findings],
            "sources": [],
            "open_questions": [],
        }
