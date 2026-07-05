"""
Google Gemini LLM provider implementation (via OpenRouter).

Uses OpenRouter's OpenAI-compatible endpoint to access Gemini models.
Supports Gemini 2.0 Flash, Gemini 1.5 Pro, Gemini 1.5 Flash, and other
Google AI models via the OpenAI async client.
"""

import logging
from typing import Any, AsyncGenerator

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam

from app.core.config import settings
from app.core.exceptions import LLMError
from app.llms.providers.base import BaseLLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class GoogleProvider(BaseLLMProvider):
    """Provider for Google Gemini language models via OpenRouter."""

    provider_name: str = "google"

    _pricing: dict[str, dict[str, float]] = {
        "gemini-2.0-flash-exp": {"input": 0.0, "output": 0.0},
        "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
        "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
        "gemini-1.5-pro-002": {"input": 1.25, "output": 5.00},
        "gemini-1.5-flash-002": {"input": 0.075, "output": 0.30},
        "poolside/laguna-m.1:free": {"input": 0.0, "output": 0.0},
    }

    def __init__(self, api_key: str | None = None) -> None:
        """
        Initialize the Google Gemini provider via OpenRouter.

        Args:
            api_key: OpenRouter API key. Falls back to settings if not provided.
        """
        resolved_key = api_key or settings.llm.google_api_key
        if not resolved_key:
            raise LLMError(
                message="Google API key is not configured. Set GOOGLE_API_KEY environment variable.",
                details={"provider": "google"},
            )
        base_url = settings.llm.google_base_url
        self._client = AsyncOpenAI(api_key=resolved_key, base_url=base_url)
        self._default_model = settings.llm.google_default_model
        logger.info("Google Gemini provider initialised with model %s via OpenRouter", self._default_model)

    def count_tokens(self, text: str) -> int:
        """Estimate token count. Gemini uses roughly 4 chars per token."""
        return len(text) // 4

    async def generate(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Generate a response via OpenRouter's OpenAI-compatible endpoint.

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

        typed_messages: list[ChatCompletionMessageParam] = [
            {"role": m["role"], "content": m["content"]} for m in messages
        ]

        try:
            response = await self._client.chat.completions.create(
                model=resolved_model,
                messages=typed_messages,
                temperature=resolved_temp,
                max_tokens=resolved_max,
                **kwargs,
            )
        except Exception as exc:
            logger.error("Google Gemini generation failed: %s", exc, exc_info=True)
            raise LLMError(
                message=f"Google Gemini API error: {exc}",
                details={"provider": "google", "model": resolved_model},
            ) from exc

        choice = response.choices[0]
        usage = response.usage
        prompt_tokens = usage.prompt_tokens if usage else 0
        completion_tokens = usage.completion_tokens if usage else 0

        return LLMResponse(
            content=choice.message.content or "",
            model=response.model,
            token_usage={
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
            finish_reason=choice.finish_reason or "stop",
            cost_usd=self._build_cost(response.model, prompt_tokens, completion_tokens),
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
        Stream a response from OpenRouter's OpenAI-compatible endpoint.

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

        typed_messages: list[ChatCompletionMessageParam] = [
            {"role": m["role"], "content": m["content"]} for m in messages
        ]

        try:
            stream = await self._client.chat.completions.create(
                model=resolved_model,
                messages=typed_messages,
                temperature=resolved_temp,
                max_tokens=resolved_max,
                stream=True,
                **kwargs,
            )
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as exc:
            logger.error("Google Gemini streaming failed: %s", exc, exc_info=True)
            raise LLMError(
                message=f"Google Gemini streaming error: {exc}",
                details={"provider": "google", "model": resolved_model},
            ) from exc
