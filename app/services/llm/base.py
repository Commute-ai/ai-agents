"""
Abstract base class for LLM providers.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Any


class LLMProvider(ABC):
    """
    Abstract interface for Large Language Model providers.

    Defines common interface for generating text using different LLM services
    like Anthropic, OpenAI, Ollama, etc.
    """

    @abstractmethod
    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize the LLM provider with configuration.

        Args:
            **kwargs: Provider-specific configuration options
        """
        pass

    @abstractmethod
    async def generate(
        self,
        messages: list[dict[str, str]],
        max_tokens: int | None = None,
        temperature: float | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Generate text response from messages.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 to 1.0)
            **kwargs: Additional provider-specific parameters

        Returns:
            Generated text response

        Raises:
            LLMError: If generation fails
        """
        pass

    @abstractmethod
    def generate_stream(
        self,
        messages: list[dict[str, str]],
        max_tokens: int | None = None,
        temperature: float | None = None,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """
        Generate streaming text response from messages.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 to 1.0)
            **kwargs: Additional provider-specific parameters

        Yields:
            Chunks of generated text

        Raises:
            LLMError: If generation fails
        """
        pass


class LLMError(Exception):
    """Base exception for LLM provider errors."""

    pass


class LLMConnectionError(LLMError):
    """Raised when unable to connect to LLM service."""

    pass


class LLMRateLimitError(LLMError):
    """Raised when rate limit is exceeded."""

    pass


class LLMValidationError(LLMError):
    """Raised when request validation fails."""

    pass
