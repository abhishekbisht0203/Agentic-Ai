"""
Anthropic LLM provider implementation.

Supports Claude 3.5 Sonnet, Claude 3 Haiku, Claude 3 Opus, and other
Anthropic models via the official async client.
"""

import logging
from typing import Any, AsyncGenerator

from anthropic import AsyncAnthropic

from app.core.config import settings
from app.core.exceptions import LLMError
from app.llms.providers.base import BaseLLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseLLMProvider):
    """Provider for Anthropic Claude language models."""

    provider_name: str = "anthropic"

    _pricing: dict[str, dict[str, float]] = {
        "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
        "claude-3-5-sonnet-20240620": {"input": 3.00, "output": 15.00},
        "claude-3-5-haiku-20241022": {"input": 0.80, "output": 4.00},
        "claude-3-opus-20240229": {"input": 15.00, "output": 75.00},
        "claude-3-sonnet-20240229": {"input": 3.00, "output": 15.00},
        "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
    }

    def __init__(self, api_key: str | None = None) -> None:
        """
        Initialize the Anthropic provider.

        Args:
            api_key: Anthropic API key. Falls back to settings if not provided.
        """
        resolved_key = api_key or settings.llm.anthropic_api_key
        if not resolved_key:
            raise LLMError(
                message="Anthropic API key is not configured. Set ANTHROPIC_API_KEY environment variable.",
                details={"provider": "anthropic"},
            )
        self._client = AsyncAnthropic(api_key=resolved_key)
        self._default_model = settings.llm.anthropic_default_model
        logger.info("Anthropic provider initialised with model %s", self._default_model)

    def count_tokens(self, text: str) -> int:
        """Estimate token count. Anthropic uses ~4 chars per token on average."""
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
        Generate a response via the Anthropic Messages API.

        The system message (if present in the first position) is extracted
        and passed as the ``system`` parameter, as required by the Anthropic API.

        Args:
            messages: Conversation messages.
            model: Model to use.
            temperature: Sampling temperature.
            max_tokens: Max completion tokens.
            **kwargs: Extra parameters forwarded to the API.

        Returns:
            Standardised LLMResponse.

        Raises:
            LLMError: On API or network errors.
        """
        resolved_model = model or self._default_model
        resolved_temp = temperature if temperature is not None else 0.7
        resolved_max = max_tokens or 4096

        system_prompt = ""
        api_messages = list(messages)
        if api_messages and api_messages[0].get("role") == "system":
            system_prompt = api_messages.pop(0)["content"]

        try:
            request_kwargs: dict[str, Any] = {
                "model": resolved_model,
                "messages": api_messages,
                "max_tokens": resolved_max,
                "temperature": resolved_temp,
            }
            if system_prompt:
                request_kwargs["system"] = system_prompt
            request_kwargs.update(kwargs)

            response = await self._client.messages.create(**request_kwargs)
        except Exception as exc:
            logger.error("Anthropic generation failed: %s", exc, exc_info=True)
            raise LLMError(
                message=f"Anthropic API error: {exc}",
                details={"provider": "anthropic", "model": resolved_model},
            ) from exc

        content = ""
        for block in response.content:
            if block.type == "text":
                content += block.text

        prompt_tokens = response.usage.input_tokens
        completion_tokens = response.usage.output_tokens

        return LLMResponse(
            content=content,
            model=response.model,
            token_usage={
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
            finish_reason=response.stop_reason or "end_turn",
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
        Stream a response from the Anthropic Messages API.

        Yields text blocks as they arrive.

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
        resolved_temp = temperature if temperature is not None else 0.7
        resolved_max = max_tokens or 4096

        system_prompt = ""
        api_messages = list(messages)
        if api_messages and api_messages[0].get("role") == "system":
            system_prompt = api_messages.pop(0)["content"]

        try:
            request_kwargs: dict[str, Any] = {
                "model": resolved_model,
                "messages": api_messages,
                "max_tokens": resolved_max,
                "temperature": resolved_temp,
            }
            if system_prompt:
                request_kwargs["system"] = system_prompt
            request_kwargs.update(kwargs)

            async with self._client.messages.stream(**request_kwargs) as stream:
                async for text in stream.text_stream:
                    yield text
        except Exception as exc:
            logger.error("Anthropic streaming failed: %s", exc, exc_info=True)
            raise LLMError(
                message=f"Anthropic streaming error: {exc}",
                details={"provider": "anthropic", "model": resolved_model},
            ) from exc
