"""
Google Gemini LLM provider implementation.

Supports Gemini 2.0 Flash, Gemini 1.5 Pro, Gemini 1.5 Flash, and other
Google AI Studio / Vertex AI models via the google-generativeai SDK.
"""

import logging
from typing import Any, AsyncGenerator

import google.generativeai as genai

from app.core.config import settings
from app.core.exceptions import LLMError
from app.llms.providers.base import BaseLLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class GoogleProvider(BaseLLMProvider):
    """Provider for Google Gemini language models."""

    provider_name: str = "google"

    _pricing: dict[str, dict[str, float]] = {
        "gemini-2.0-flash-exp": {"input": 0.0, "output": 0.0},
        "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
        "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
        "gemini-1.5-pro-002": {"input": 1.25, "output": 5.00},
        "gemini-1.5-flash-002": {"input": 0.075, "output": 0.30},
    }

    def __init__(self, api_key: str | None = None) -> None:
        """
        Initialize the Google Gemini provider.

        Args:
            api_key: Google AI API key. Falls back to settings if not provided.
        """
        resolved_key = api_key or settings.llm.google_api_key
        if not resolved_key:
            raise LLMError(
                message="Google API key is not configured. Set GOOGLE_API_KEY environment variable.",
                details={"provider": "google"},
            )
        genai.configure(api_key=resolved_key)
        self._default_model = settings.llm.google_default_model
        logger.info("Google Gemini provider initialised with model %s", self._default_model)

    def count_tokens(self, text: str) -> int:
        """Estimate token count. Gemini uses roughly 4 chars per token."""
        return len(text) // 4

    def _convert_messages(
        self, messages: list[dict[str, str]]
    ) -> tuple[str, list[dict[str, Any]]]:
        """
        Convert generic message format to Gemini's format.

        Extracts the system instruction (if present) and converts the
        remaining messages into Gemini content dicts.

        Returns:
            Tuple of (system_instruction, contents).
        """
        system_instruction = ""
        contents: list[dict[str, Any]] = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                system_instruction = content
            elif role == "assistant":
                contents.append({"role": "model", "parts": [content]})
            else:
                contents.append({"role": "user", "parts": [content]})

        return system_instruction, contents

    async def generate(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Generate a response via the Google Gemini API.

        Args:
            messages: Conversation messages.
            model: Model to use.
            temperature: Sampling temperature.
            max_tokens: Max output tokens.
            **kwargs: Extra parameters forwarded to the API.

        Returns:
            Standardised LLMResponse.

        Raises:
            LLMError: On API or network errors.
        """
        resolved_model = model or self._default_model
        resolved_temp = temperature if temperature is not None else 0.7
        resolved_max = max_tokens or 4096

        system_instruction, contents = self._convert_messages(messages)

        try:
            genai_model = genai.GenerativeModel(
                model_name=resolved_model,
                system_instruction=system_instruction or None,
            )

            generation_config = genai.types.GenerationConfig(
                temperature=resolved_temp,
                max_output_tokens=resolved_max,
            )

            response = await genai_model.generate_content_async(
                contents=contents,
                generation_config=generation_config,
            )
        except Exception as exc:
            logger.error("Google Gemini generation failed: %s", exc, exc_info=True)
            raise LLMError(
                message=f"Google Gemini API error: {exc}",
                details={"provider": "google", "model": resolved_model},
            ) from exc

        content = response.text or ""
        prompt_tokens = 0
        completion_tokens = 0
        if response.usage_metadata:
            prompt_tokens = getattr(response.usage_metadata, "prompt_token_count", 0) or 0
            completion_tokens = getattr(response.usage_metadata, "candidates_token_count", 0) or 0

        finish_reason = "stop"
        if response.candidates and response.candidates[0].finish_reason:
            finish_reason = str(response.candidates[0].finish_reason)

        return LLMResponse(
            content=content,
            model=resolved_model,
            token_usage={
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
            finish_reason=finish_reason,
            cost_usd=self._build_cost(resolved_model, prompt_tokens, completion_tokens),
            raw_response=response,
        )

    async def generate_stream(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """
        Stream a response from the Google Gemini API.

        Yields content chunks as they are generated.

        Args:
            messages: Conversation messages.
            model: Model to use.
            temperature: Sampling temperature.
            max_tokens: Max output tokens.
            **kwargs: Extra parameters forwarded to the API.

        Yields:
            String content chunks.

        Raises:
            LLMError: On API or network errors.
        """
        resolved_model = model or self._default_model
        resolved_temp = temperature if temperature is not None else 0.7
        resolved_max = max_tokens or 4096

        system_instruction, contents = self._convert_messages(messages)

        try:
            genai_model = genai.GenerativeModel(
                model_name=resolved_model,
                system_instruction=system_instruction or None,
            )

            generation_config = genai.types.GenerationConfig(
                temperature=resolved_temp,
                max_output_tokens=resolved_max,
            )

            async for chunk in await genai_model.generate_content_async(
                contents=contents,
                generation_config=generation_config,
                stream=True,
            ):
                if chunk.text:
                    yield chunk.text
        except Exception as exc:
            logger.error("Google Gemini streaming failed: %s", exc, exc_info=True)
            raise LLMError(
                message=f"Google Gemini streaming error: {exc}",
                details={"provider": "google", "model": resolved_model},
            ) from exc
