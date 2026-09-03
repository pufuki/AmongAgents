"""LLM provider abstraction.

Defines the interface that all LLM providers must implement.
The game engine and agents never call a specific provider directly;
they use this interface so a new provider can be added without
modifying game logic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name for logging."""
        ...

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        """True if the provider has valid API credentials."""
        ...

    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> dict:
        """Send a request and return parsed JSON dict.

        Raises:
            LLMError: on any failure (network, auth, parse).
        """
        ...


class LLMError(Exception):
    """Raised when an LLM provider call fails."""
    pass


class NoAPIKeyError(LLMError):
    """Raised when no API key is configured."""
    pass


def get_provider() -> Optional[LLMProvider]:
    """Factory: return the configured LLM provider, or None if none available.

    Reads LLM_PROVIDER from environment. Falls back to mock/no-provider mode
    if no API key is set.
    """
    import os

    provider_name = os.getenv("LLM_PROVIDER", "openrouter").lower()

    if provider_name == "openrouter":
        from app.llm.openrouter import OpenRouterProvider
        return OpenRouterProvider()

    if provider_name == "groq":
        from app.llm.groq import GroqProvider
        return GroqProvider()

    # Default: try openrouter
    from app.llm.openrouter import OpenRouterProvider
    return OpenRouterProvider()
