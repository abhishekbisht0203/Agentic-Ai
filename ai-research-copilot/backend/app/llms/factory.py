"""
Factory for creating and managing LLM provider instances.

Centralises provider creation, caching, and default-model resolution.
"""

import logging
from typing import Any

from app.llms.providers.base import BaseLLMProvider

logger = logging.getLogger(__name__)

# Lazy-loaded provider registry: provider_name → class
_PROVIDER_CLASSES: dict[str, type[BaseLLMProvider]] = {}


def _load_providers() -> None:
    """Populate the registry on first use."""
    if _PROVIDER_CLASSES:
        return
    try:
        from app.llms.providers.openai_provider import OpenAIProvider

        _PROVIDER_CLASSES["openai"] = OpenAIProvider
    except ImportError:
        logger.debug("OpenAI provider not available")
    try:
        from app.llms.providers.anthropic_provider import AnthropicProvider

        _PROVIDER_CLASSES["anthropic"] = AnthropicProvider
    except ImportError:
        logger.debug("Anthropic provider not available")
    try:
        from app.llms.providers.google_provider import GoogleProvider

        _PROVIDER_CLASSES["google"] = GoogleProvider
    except ImportError:
        logger.debug("Google provider not available")


class LLMFactory:
    """Create and cache LLM provider instances.

    Usage::

        factory = LLMFactory(default_provider="openai")
        provider = factory.get_provider()              # uses default
        provider = factory.get_provider("anthropic")   # explicit override
    """

    _instances: dict[str, BaseLLMProvider] = {}

    def __init__(
        self,
        default_provider: str = "openai",
        default_model: str | None = None,
        provider_configs: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        self.default_provider = default_provider
        self.default_model = default_model
        self.provider_configs = provider_configs or {}

    def get_provider(self, provider_name: str | None = None) -> BaseLLMProvider:
        """Return (or create) an LLM provider instance.

        Parameters
        ----------
        provider_name : str | None
            Provider key.  Falls back to ``self.default_provider`` when *None*.

        Returns
        -------
        BaseLLMProvider
            A ready-to-use provider instance.

        Raises
        ------
        ValueError
            If the requested provider is not registered.
        """
        _load_providers()
        name = provider_name or self.default_provider

        if name not in _PROVIDER_CLASSES:
            available = list(_PROVIDER_CLASSES.keys())
            raise ValueError(
                f"Unknown LLM provider '{name}'. Available: {available}"
            )

        if name not in self._instances:
            config = self.provider_configs.get(name, {})
            if self.default_model and "model" not in config:
                config["model"] = self.default_model
            self._instances[name] = _PROVIDER_CLASSES[name](**config)
            logger.info("Created LLM provider: %s", name)

        return self._instances[name]

    @classmethod
    def register_provider(
        cls, name: str, provider_class: type[BaseLLMProvider]
    ) -> None:
        """Manually register a provider class."""
        _PROVIDER_CLASSES[name] = provider_class
        logger.info("Registered LLM provider: %s", name)

    @classmethod
    def list_providers(cls) -> list[str]:
        """Return names of all registered providers."""
        _load_providers()
        return list(_PROVIDER_CLASSES.keys())

    def __repr__(self) -> str:
        return (
            f"LLMFactory(default_provider={self.default_provider!r}, "
            f"available={self.list_providers()})"
        )
