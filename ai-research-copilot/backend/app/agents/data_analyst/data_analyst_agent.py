"""
Data Analyst agent – analyses data and produces insights, statistics,
and visualisation suggestions.
"""

import json
import uuid
import logging
from typing import Any

from app.agents.base.agent import BaseAgent
from app.llms.providers.base import BaseLLMProvider
from app.llms.prompts.templates import DATA_ANALYST_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class DataAnalystAgent(BaseAgent):
    """Analyses data provided in the input and returns structured insights.

    The agent can handle:
    - Raw data pasted as CSV, JSON, or tabular text.
    - Descriptions of datasets (schema, summary stats).
    - Questions about specific data points or trends.
    """

    agent_type: str = "data_analyst"

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
        """Analyse the data in ``input_data`` and return insights.

        Parameters
        ----------
        input_data : dict
            ``"message"``: question or instruction about the data.
            ``"data"`` (optional): raw data (str, list, or dict).
            ``"data_description"`` (optional): schema / column info.
            ``"analysis_type"`` (optional): ``"descriptive"`` | ``"diagnostic"`` | ``"predictive"``.

        Returns
        -------
        dict
            ``{"dataset_summary": …, "statistics": …, "insights": …,
            "visualisation_suggestions": …, "recommendations": …}``
        """
        message = input_data.get("message", "")
        data = input_data.get("data")
        data_description = input_data.get("data_description", "")

        if not message and data is None:
            return {
                "dataset_summary": {},
                "statistics": {},
                "insights": [],
                "visualisation_suggestions": [],
                "recommendations": [],
                "error": "No message or data provided.",
            }

        self.logger.info("Data analyst processing: %r", message[:120])
        self.memory.add("user", message or "Analyse the provided data")

        analysis_type = input_data.get("analysis_type", "descriptive")

        # Step 1 – describe the dataset
        dataset_summary = await self._summarise_dataset(data, data_description)

        # Step 2 – compute statistics
        statistics = await self._compute_statistics(data, data_description, analysis_type)

        # Step 3 – generate insights
        insights = await self._generate_insights(
            message, data, data_description, dataset_summary, statistics
        )

        # Step 4 – suggest visualisations
        visualisations = await self._suggest_visualisations(
            data, data_description, statistics
        )

        # Step 5 – actionable recommendations
        recommendations = await self._generate_recommendations(
            message, insights, statistics
        )

        result = {
            "dataset_summary": dataset_summary,
            "statistics": statistics,
            "insights": insights,
            "visualisation_suggestions": visualisations,
            "recommendations": recommendations,
        }

        self.memory.add("assistant", json.dumps(result, default=str))
        return result

    # ------------------------------------------------------------------
    # Internal steps
    # ------------------------------------------------------------------

    async def _summarise_dataset(
        self, data: Any, data_description: str
    ) -> dict[str, Any]:
        """Produce a high-level summary of the dataset."""
        prompt = self._build_data_context("Summarise this dataset.", data, data_description)
        messages = self._build_messages(DATA_ANALYST_SYSTEM_PROMPT, prompt)
        try:
            response = await self._generate_response(messages, temperature=0.3, max_tokens=1000)
            parsed = self._parse_json_response(response)
            if isinstance(parsed, dict):
                return parsed
            return {"description": response.content[:500]}
        except Exception:
            self.logger.exception("Dataset summarisation failed")
            return {"description": "Unable to summarise dataset."}

    async def _compute_statistics(
        self, data: Any, data_description: str, analysis_type: str
    ) -> dict[str, Any]:
        """Compute relevant summary statistics."""
        prompt = (
            self._build_data_context(
                f"Compute summary statistics (analysis type: {analysis_type}).",
                data,
                data_description,
            )
            + "\n\nRespond with a JSON object of statistics."
        )
        messages = self._build_messages(DATA_ANALYST_SYSTEM_PROMPT, prompt)
        try:
            response = await self._generate_response(messages, temperature=0.2, max_tokens=1500)
            parsed = self._parse_json_response(response)
            if isinstance(parsed, dict):
                return parsed
            return {"raw": response.content[:1000]}
        except Exception:
            self.logger.exception("Statistics computation failed")
            return {"error": "Unable to compute statistics."}

    async def _generate_insights(
        self,
        question: str,
        data: Any,
        data_description: str,
        summary: dict,
        statistics: dict,
    ) -> list[str]:
        """Generate analytical insights from the data."""
        prompt = (
            self._build_data_context(
                f"Generate insights for: {question}", data, data_description
            )
            + f"\n\nDataset summary: {json.dumps(summary, default=str)[:2000]}"
            + f"\n\nStatistics: {json.dumps(statistics, default=str)[:2000]}"
            + "\n\nList your key insights as a JSON array of strings."
        )
        messages = self._build_messages(DATA_ANALYST_SYSTEM_PROMPT, prompt)
        try:
            response = await self._generate_response(messages, temperature=0.4, max_tokens=1500)
            parsed = self._parse_json_response(response)
            if isinstance(parsed, list):
                return [str(i) for i in parsed]
            if isinstance(parsed, dict) and "insights" in parsed:
                return [str(i) for i in parsed["insights"]]
            return [response.content[:500]]
        except Exception:
            self.logger.exception("Insight generation failed")
            return ["Unable to generate insights."]

    async def _suggest_visualisations(
        self, data: Any, data_description: str, statistics: dict
    ) -> list[dict[str, str]]:
        """Suggest appropriate visualisations for the data."""
        prompt = (
            self._build_data_context(
                "Suggest the best visualisations for this data.",
                data,
                data_description,
            )
            + f"\n\nStatistics: {json.dumps(statistics, default=str)[:1500]}"
            + "\n\nRespond with a JSON array of objects: "
            '[{"chart_type": "...", "title": "...", "description": "...", '
            '"columns": ["..."]}]'
        )
        messages = self._build_messages(DATA_ANALYST_SYSTEM_PROMPT, prompt)
        try:
            response = await self._generate_response(messages, temperature=0.3, max_tokens=1500)
            parsed = self._parse_json_response(response)
            if isinstance(parsed, list):
                return parsed
            if isinstance(parsed, dict) and "visualisation_suggestions" in parsed:
                return parsed["visualisation_suggestions"]
            return [{"chart_type": "text", "title": "Summary", "description": response.content[:300]}]
        except Exception:
            self.logger.exception("Visualisation suggestion failed")
            return []

    async def _generate_recommendations(
        self, question: str, insights: list[str], statistics: dict
    ) -> list[str]:
        """Produce actionable recommendations."""
        prompt = (
            f"Based on the following, provide actionable recommendations.\n\n"
            f"User question: {question}\n\n"
            f"Insights:\n" + "\n".join(f"- {i}" for i in insights) + "\n\n"
            f"Statistics: {json.dumps(statistics, default=str)[:1500]}\n\n"
            "Return a JSON array of recommendation strings."
        )
        messages = self._build_messages(DATA_ANALYST_SYSTEM_PROMPT, prompt)
        try:
            response = await self._generate_response(messages, temperature=0.4, max_tokens=1000)
            parsed = self._parse_json_response(response)
            if isinstance(parsed, list):
                return [str(r) for r in parsed]
            if isinstance(parsed, dict) and "recommendations" in parsed:
                return [str(r) for r in parsed["recommendations"]]
            return [response.content[:500]]
        except Exception:
            self.logger.exception("Recommendation generation failed")
            return ["Unable to generate recommendations."]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_data_context(instruction: str, data: Any, data_description: str) -> str:
        """Construct a prompt that includes the data or its description."""
        parts = [instruction]
        if data is not None:
            if isinstance(data, str):
                data_str = data[:5000]
            elif isinstance(data, (list, dict)):
                data_str = json.dumps(data, default=str)[:5000]
            else:
                data_str = str(data)[:5000]
            parts.append(f"\nData:\n{data_str}")
        if data_description:
            parts.append(f"\nData description:\n{data_description[:2000]}")
        return "\n".join(parts)
