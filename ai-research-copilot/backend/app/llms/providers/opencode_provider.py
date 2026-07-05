"""
OpenCode + Zen API LLM provider implementation.

Uses the OpenAI-compatible API provided by OpenCode's Zen API service.
Supports all OpenAI chat models via the Zen API endpoint.
"""

import logging
from typing import Any, AsyncGenerator

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam

from app.core.config import settings
from app.core.exceptions import LLMError
from app.llms.providers.base import BaseLLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class OpenCodeProvider(BaseLLMProvider):
    """Provider for OpenCode + Zen API language models."""

    provider_name: str = "opencode"

    _pricing: dict[str, dict[str, float]] = {
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4-turbo": {"input": 10.00, "output": 30.00},
        "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    }

    def __init__(self, api_key: str | None = None) -> None:
        """
        Initialize the OpenCode provider.

        Args:
            api_key: API key for Zen API. Falls back to settings if not provided.
        """
        resolved_key = api_key or settings.llm.opencode_api_key
        if not resolved_key:
            raise LLMError(
                message="OpenCode API key is not configured. Set OPENCODE_API_KEY environment variable.",
                details={"provider": "opencode"},
            )
        base_url = settings.llm.opencode_base_url
        self._client = AsyncOpenAI(api_key=resolved_key, base_url=base_url)
        self._default_model = settings.llm.opencode_default_model
        logger.info("OpenCode provider initialised with model %s", self._default_model)

    def count_tokens(self, text: str) -> int:
        """Estimate token count using a simple heuristic."""
        return len(text) // 4

    async def generate(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a chat completion via the OpenCode Zen API."""
        resolved_model = model or self._default_model
        resolved_temp = temperature if temperature is not None else settings.llm.opencode_temperature
        resolved_max = max_tokens or settings.llm.opencode_max_tokens

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
            logger.error("OpenCode generation failed: %s", exc, exc_info=True)
            raise LLMError(
                message=f"OpenCode API error: {exc}",
                details={"provider": "opencode", "model": resolved_model},
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
        """Stream a chat completion from the OpenCode Zen API."""
        resolved_model = model or self._default_model
        resolved_temp = temperature if temperature is not None else settings.llm.opencode_temperature
        resolved_max = max_tokens or settings.llm.opencode_max_tokens

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
            logger.error("OpenCode streaming failed: %s", exc, exc_info=True)
            raise LLMError(
                message=f"OpenCode streaming error: {exc}",
                details={"provider": "opencode", "model": resolved_model},
            ) from exc
