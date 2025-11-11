"""
Utility functions for LLM service initialization.
"""

from app.config import settings

from .base import LLMProvider
from .factory import LLMProviderFactory


def create_llm_from_config() -> LLMProvider:
    """
    Create an LLM provider instance from application configuration.

    Returns:
        Initialized LLM provider instance based on config settings

    Raises:
        ValueError: If provider configuration is invalid or missing
    """
    provider_name = settings.LLM_PROVIDER.lower()

    if provider_name == "groq":
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is required when using Groq provider")

        return LLMProviderFactory.create_provider(
            "groq",
            api_key=settings.GROQ_API_KEY,
            model=settings.GROQ_MODEL,
        )

    elif provider_name == "openai":
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required when using OpenAI provider")

        return LLMProviderFactory.create_provider(
            "openai",
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
        )

    else:
        available = LLMProviderFactory.get_available_providers()
        raise ValueError(
            f"Unsupported LLM provider: {provider_name}. "
            f"Available providers: {', '.join(available)}"
        )
