"""
Abstract base class for all LLM providers.

Defines the interface that all LLM provider implementations must follow,
ensuring consistent behavior across different AI model backends.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """Standardized response from any LLM provider."""

    content: str
    model: str
    token_usage: dict[str, int] = field(
        default_factory=lambda: {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }
    )
    finish_reason: str = "stop"
    cost_usd: float | None = None
    raw_response: Any = None


class BaseLLMProvider(ABC):
    """
    Abstract base class for all LLM providers.

    Every provider (OpenAI, Anthropic, Google, Ollama) must implement
    these methods to provide a uniform interface for the rest of the application.
    """

    provider_name: str = "base"

    # Approximate pricing per 1M tokens (USD). Subclasses override.
    _pricing: dict[str, dict[str, float]] = {}

    @abstractmethod
    async def generate(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Generate a completion from the LLM.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            model: Model identifier; uses provider default when None.
            temperature: Sampling temperature (0.0-2.0).
            max_tokens: Maximum tokens in the completion.
            **kwargs: Provider-specific additional parameters.

        Returns:
            LLMResponse with content, token usage, and metadata.

        Raises:
            LLMError: If the provider returns an error.
        """
        ...

    @abstractmethod
    async def generate_stream(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """
        Stream a completion from the LLM.

        Yields content chunks as they are generated.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            model: Model identifier; uses provider default when None.
            temperature: Sampling temperature (0.0-2.0).
            max_tokens: Maximum tokens in the completion.
            **kwargs: Provider-specific additional parameters.

        Yields:
            String chunks of the generated content.

        Raises:
            LLMError: If the provider returns an error during streaming.
        """
        ...
        yield  # pragma: no cover – makes this an async generator

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """
        Estimate the token count for the given text.

        Args:
            text: Input text to tokenize.

        Returns:
            Approximate number of tokens.
        """
        ...

    def calculate_cost(
        self, model: str, prompt_tokens: int, completion_tokens: int
    ) -> float | None:
        """
        Calculate the cost in USD for a request based on token counts.

        Args:
            model: The model identifier used.
            prompt_tokens: Number of input tokens.
            completion_tokens: Number of output tokens.

        Returns:
            Cost in USD, or None if pricing data is unavailable for the model.
        """
        pricing = self._pricing.get(model)
        if pricing is None:
            return None
        input_cost = (prompt_tokens / 1_000_000) * pricing.get("input", 0)
        output_cost = (completion_tokens / 1_000_000) * pricing.get("output", 0)
        return round(input_cost + output_cost, 8)

    def _build_cost(
        self, model: str, prompt_tokens: int, completion_tokens: int
    ) -> float | None:
        """Convenience wrapper used by concrete providers."""
        return self.calculate_cost(model, prompt_tokens, completion_tokens)
