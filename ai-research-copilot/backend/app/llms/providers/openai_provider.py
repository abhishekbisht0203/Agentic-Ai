"""
OpenAI LLM provider implementation.

Supports GPT-4o, GPT-4o-mini, GPT-4-turbo, and other OpenAI chat models.
Uses the official openai async client for HTTP communication.
"""

import logging
from typing import Any, AsyncGenerator

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam

from app.core.config import settings
from app.core.exceptions import LLMError
from app.llms.providers.base import BaseLLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """Provider for OpenAI language models."""

    provider_name: str = "openai"

    _pricing: dict[str, dict[str, float]] = {
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "gpt-4o-2024-05-13": {"input": 5.00, "output": 15.00},
        "gpt-4o-2024-08-06": {"input": 2.50, "output": 10.00},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4o-mini-2024-07-18": {"input": 0.15, "output": 0.60},
        "gpt-4-turbo": {"input": 10.00, "output": 30.00},
        "gpt-4-turbo-preview": {"input": 10.00, "output": 30.00},
        "gpt-4": {"input": 30.00, "output": 60.00},
        "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
        "o1": {"input": 15.00, "output": 60.00},
        "o1-mini": {"input": 3.00, "output": 12.00},
        "o1-preview": {"input": 15.00, "output": 60.00},
        "o3-mini": {"input": 1.10, "output": 4.40},
    }

    def __init__(self, api_key: str | None = None) -> None:
        """
        Initialize the OpenAI provider.

        Args:
            api_key: OpenAI API key. Falls back to settings if not provided.
        """
        resolved_key = api_key or settings.llm.openai_api_key
        if not resolved_key:
            raise LLMError(
                message="OpenAI API key is not configured. Set OPENAI_API_KEY environment variable.",
                details={"provider": "openai"},
            )
        base_url = settings.llm.openai_base_url
        self._client = AsyncOpenAI(api_key=resolved_key, base_url=base_url)
        self._default_model = settings.llm.openai_default_model
        logger.info("OpenAI provider initialised with model %s", self._default_model)

    def count_tokens(self, text: str) -> int:
        """
        Estimate token count using a simple heuristic.

        OpenAI does not expose a free tokenizer; this approximation
        works well enough for budgeting context windows.
        """
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
        Generate a chat completion via the OpenAI API.

        Args:
            messages: Conversation messages.
            model: Model to use; defaults to configured default.
            temperature: Sampling temperature.
            max_tokens: Max completion tokens.
            **kwargs: Extra parameters forwarded to the API.

        Returns:
            Standardised LLMResponse.

        Raises:
            LLMError: On API or network errors.
        """
        resolved_model = model or self._default_model
        resolved_temp = temperature if temperature is not None else settings.llm.openai_temperature
        resolved_max = max_tokens or settings.llm.openai_max_tokens

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
            logger.error("OpenAI generation failed: %s", exc, exc_info=True)
            raise LLMError(
                message=f"OpenAI API error: {exc}",
                details={"provider": "openai", "model": resolved_model},
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
        Stream a chat completion from the OpenAI API.

        Yields content chunks as they arrive from the server.

        Args:
            messages: Conversation messages.
            model: Model to use.
            temperature: Sampling temperature.
            max_tokens: Max completion tokens.
            **kwargs: Extra parameters forwarded to the API.

        Yields:
            String content chunks.

        Raises:
            LLMError: On API or network errors.
        """
        resolved_model = model or self._default_model
        resolved_temp = temperature if temperature is not None else settings.llm.openai_temperature
        resolved_max = max_tokens or settings.llm.openai_max_tokens

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
            logger.error("OpenAI streaming failed: %s", exc, exc_info=True)
            raise LLMError(
                message=f"OpenAI streaming error: {exc}",
                details={"provider": "openai", "model": resolved_model},
            ) from exc
