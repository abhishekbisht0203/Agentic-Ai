"""
Ollama LLM provider implementation.

Provides access to locally-running Ollama models (Llama, Mistral, etc.)
via the Ollama HTTP API using httpx for async communication.
"""

import json
import logging
from typing import Any, AsyncGenerator

import httpx

from app.core.config import settings
from app.core.exceptions import LLMError
from app.llms.providers.base import BaseLLMProvider, LLMResponse

logger = logging.getLogger(__name__)

# Timeout for normal requests (generation can be slow for large models)
_DEFAULT_TIMEOUT = httpx.Timeout(120.0, connect=10.0)
_STREAM_TIMEOUT = httpx.Timeout(300.0, connect=10.0)


class OllamaProvider(BaseLLMProvider):
    """Provider for locally-hosted Ollama language models."""

    provider_name: str = "ollama"

    def __init__(self, base_url: str | None = None) -> None:
        """
        Initialize the Ollama provider.

        Args:
            base_url: Base URL for the Ollama API. Defaults to settings value.
        """
        self._base_url = (base_url or settings.llm.ollama_base_url).rstrip("/")
        self._default_model = settings.llm.ollama_default_model
        logger.info(
            "Ollama provider initialised – endpoint %s, model %s",
            self._base_url,
            self._default_model,
        )

    def count_tokens(self, text: str) -> int:
        """Rough token estimate (~4 chars per token)."""
        return len(text) // 4

    async def _check_connection(self) -> None:
        """Verify that the Ollama server is reachable."""
        try:
            async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT) as client:
                resp = await client.get(f"{self._base_url}/api/tags")
                resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise LLMError(
                message=f"Cannot reach Ollama at {self._base_url}: {exc}",
                details={"provider": "ollama", "base_url": self._base_url},
            ) from exc

    async def generate(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Generate a response via the Ollama /api/chat endpoint.

        Args:
            messages: Conversation messages.
            model: Model to use.
            temperature: Sampling temperature.
            max_tokens: Not directly supported by Ollama; forwarded as ``num_predict``.
            **kwargs: Extra parameters forwarded to the API.

        Returns:
            Standardised LLMResponse.

        Raises:
            LLMError: On connection or generation errors.
        """
        resolved_model = model or self._default_model
        resolved_temp = temperature if temperature is not None else 0.7

        payload: dict[str, Any] = {
            "model": resolved_model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": resolved_temp,
            },
        }
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        if kwargs:
            payload["options"].update(kwargs)

        try:
            async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT) as client:
                resp = await client.post(f"{self._base_url}/api/chat", json=payload)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPStatusError as exc:
            logger.error("Ollama HTTP error %s: %s", exc.response.status_code, exc)
            raise LLMError(
                message=f"Ollama returned HTTP {exc.response.status_code}: {exc}",
                details={"provider": "ollama", "model": resolved_model},
            ) from exc
        except httpx.HTTPError as exc:
            logger.error("Ollama connection error: %s", exc, exc_info=True)
            raise LLMError(
                message=f"Ollama connection error: {exc}",
                details={"provider": "ollama", "model": resolved_model},
            ) from exc

        content = data.get("message", {}).get("content", "")
        prompt_tokens = data.get("prompt_eval_count", 0)
        completion_tokens = data.get("eval_count", 0)

        return LLMResponse(
            content=content,
            model=data.get("model", resolved_model),
            token_usage={
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
            finish_reason="stop",
            cost_usd=0.0,
            raw_response=data,
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
        Stream a response from the Ollama /api/chat endpoint.

        Yields content tokens as they arrive via newline-delimited JSON.

        Args:
            messages: Conversation messages.
            model: Model to use.
            temperature: Sampling temperature.
            max_tokens: Max tokens (forwarded as ``num_predict``).
            **kwargs: Extra parameters forwarded to the API.

        Yields:
            String content chunks.

        Raises:
            LLMError: On connection or generation errors.
        """
        resolved_model = model or self._default_model
        resolved_temp = temperature if temperature is not None else 0.7

        payload: dict[str, Any] = {
            "model": resolved_model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": resolved_temp,
            },
        }
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        if kwargs:
            payload["options"].update(kwargs)

        try:
            async with httpx.AsyncClient(timeout=_STREAM_TIMEOUT) as client:
                async with client.stream(
                    "POST", f"{self._base_url}/api/chat", json=payload
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            chunk = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        if chunk.get("done"):
                            break
                        token = chunk.get("message", {}).get("content", "")
                        if token:
                            yield token
        except httpx.HTTPStatusError as exc:
            logger.error("Ollama streaming HTTP error %s: %s", exc.response.status_code, exc)
            raise LLMError(
                message=f"Ollama streaming HTTP {exc.response.status_code}: {exc}",
                details={"provider": "ollama", "model": resolved_model},
            ) from exc
        except httpx.HTTPError as exc:
            logger.error("Ollama streaming connection error: %s", exc, exc_info=True)
            raise LLMError(
                message=f"Ollama streaming connection error: {exc}",
                details={"provider": "ollama", "model": resolved_model},
            ) from exc

    async def list_models(self) -> list[str]:
        """
        List all models available on the local Ollama instance.

        Returns:
            List of model name strings.
        """
        try:
            async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT) as client:
                resp = await client.get(f"{self._base_url}/api/tags")
                resp.raise_for_status()
                data = resp.json()
                return [m["name"] for m in data.get("models", [])]
        except httpx.HTTPError as exc:
            logger.error("Failed to list Ollama models: %s", exc)
            return []
