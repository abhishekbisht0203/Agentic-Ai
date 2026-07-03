"""
Critic agent – evaluates content quality and provides structured feedback.
"""

import json
import uuid
import logging
from typing import Any

from app.agents.base.agent import BaseAgent
from app.llms.providers.base import BaseLLMProvider
from app.llms.prompts.templates import CRITIC_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class CriticAgent(BaseAgent):
    """Reviews content and returns a quality assessment with actionable feedback.

    Capabilities:
    - Factual accuracy check (based on provided context or general knowledge).
    - Logical coherence and argument structure analysis.
    - Readability and style evaluation.
    - Overall quality scoring (1-10).
    """

    agent_type: str = "critic"

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
        """Evaluate the content provided in ``input_data``.

        Parameters
        ----------
        input_data : dict
            ``"message"`` (optional): additional instructions for the review.
            ``"content"``: the text to evaluate.
            ``"criteria"`` (optional): list of specific criteria to assess.
            ``"reference"`` (optional): reference text for fact-checking.

        Returns
        -------
        dict
            ``{"score": …, "strengths": …, "weaknesses": …, "suggestions": …,
            "summary": …}``
        """
        message = input_data.get("message", "")
        content = input_data.get("content", "")
        criteria = input_data.get("criteria", [])
        reference = input_data.get("reference", "")

        if not content:
            return {
                "score": 0,
                "strengths": [],
                "weaknesses": [],
                "suggestions": [],
                "summary": "No content provided for evaluation.",
                "error": "No content provided.",
            }

        self.logger.info("Critic agent reviewing %d chars of content", len(content))
        self.memory.add("user", message or f"Review the following content ({len(content)} chars)")

        # Step 1 – overall evaluation
        evaluation = await self._evaluate_content(content, criteria, reference)

        # Step 2 – detailed feedback
        detailed = await self._detailed_feedback(content, evaluation)

        # Merge
        result = {**evaluation}
        result["detailed_feedback"] = detailed

        self.memory.add("assistant", json.dumps(result, default=str))
        return result

    # ------------------------------------------------------------------
    # Internal steps
    # ------------------------------------------------------------------

    async def _evaluate_content(
        self, content: str, criteria: list[str], reference: str
    ) -> dict[str, Any]:
        """Produce the primary evaluation of the content."""
        prompt_parts = [
            "Evaluate the following content for quality, accuracy, and clarity.",
        ]
        if criteria:
            prompt_parts.append(
                "Pay special attention to these criteria: "
                + ", ".join(criteria)
            )
        if reference:
            prompt_parts.append(
                f"\nReference material for fact-checking:\n{reference[:3000]}"
            )
        prompt_parts.append(f"\nContent to evaluate:\n{content[:6000]}")
        prompt_parts.append(
            "\nRespond with a JSON object: "
            '{"score": <1-10>, "strengths": [...], "weaknesses": [...], '
            '"suggestions": [...], "summary": "..."}'
        )

        prompt = "\n\n".join(prompt_parts)
        messages = self._build_messages(CRITIC_SYSTEM_PROMPT, prompt)

        try:
            response = await self._generate_response(messages, temperature=0.3, max_tokens=2000)
            parsed = self._parse_json_response(response)
            if isinstance(parsed, dict):
                parsed.setdefault("score", 5)
                parsed.setdefault("strengths", [])
                parsed.setdefault("weaknesses", [])
                parsed.setdefault("suggestions", [])
                parsed.setdefault("summary", "")
                # Ensure score is an integer
                try:
                    parsed["score"] = max(1, min(10, int(parsed["score"])))
                except (ValueError, TypeError):
                    parsed["score"] = 5
                return parsed
        except Exception:
            self.logger.exception("Content evaluation failed")

        return {
            "score": 5,
            "strengths": [],
            "weaknesses": ["Evaluation failed."],
            "suggestions": [],
            "summary": "Unable to complete evaluation.",
        }

    async def _detailed_feedback(
        self, content: str, evaluation: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate paragraph-level feedback for the content."""
        prompt = (
            "Provide detailed, paragraph-level feedback on the following content.\n"
            "For each paragraph or section, note what works and what could improve.\n\n"
            f"Content:\n{content[:6000]}\n\n"
            f"Initial evaluation summary: {evaluation.get('summary', '')}\n\n"
            "Respond with a JSON object:\n"
            '{"paragraph_feedback": [{"section": "...", "feedback": "...", '
            '"rating": "good|needs_work|poor"}], "style_notes": [...], '
            '"structural_notes": [...]}'
        )
        messages = self._build_messages(CRITIC_SYSTEM_PROMPT, prompt)
        try:
            response = await self._generate_response(messages, temperature=0.3, max_tokens=2000)
            parsed = self._parse_json_response(response)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            self.logger.exception("Detailed feedback generation failed")

        return {"paragraph_feedback": [], "style_notes": [], "structural_notes": []}
