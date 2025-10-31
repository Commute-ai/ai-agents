"""
Factory for creating LLM provider instances.
"""

from .base import LLMProvider
from .providers.groq import GroqProvider
from .providers.openai import OpenAIProvider


class LLMProviderFactory:
    """
    Factory class for creating LLM provider instances based on configuration.
    """

    _providers: dict[str, type[LLMProvider]] = {
        "openai": OpenAIProvider,
        "groq": GroqProvider,
    }

    @classmethod
    def create_provider(cls, provider_name: str, **kwargs) -> LLMProvider:
        """
        Create an LLM provider instance.

        Args:
            provider_name: Name of the provider ("anthropic", "openai", "ollama")
            **kwargs: Provider-specific configuration options

        Returns:
            Initialized LLM provider instance

        Raises:
            ValueError: If provider_name is not supported
        """
        if provider_name not in cls._providers:
            available = ", ".join(cls._providers.keys())
            raise ValueError(
                f"Unsupported LLM provider: {provider_name}. Available providers: {available}"
            )

        provider_class = cls._providers[provider_name]
        return provider_class(**kwargs)

    @classmethod
    def get_available_providers(cls) -> list[str]:
        """
        Get list of available provider names.

        Returns:
            List of supported provider names
        """
        return list(cls._providers.keys())


def create_llm_provider(provider_name: str, **kwargs) -> LLMProvider:
    """
    Convenience function to create an LLM provider.

    Args:
        provider_name: Name of the provider
        **kwargs: Provider-specific configuration

    Returns:
        Initialized LLM provider instance
    """
    return LLMProviderFactory.create_provider(provider_name, **kwargs)
