"""
Factory for creating LLM provider instances.
"""

from enum import Enum

from .base import LLMProvider
from .providers.groq import GroqProvider


class LLMProviderType(str, Enum):
    GROQ = "groq"


class LLMProviderFactory:
    """
    Factory class for creating LLM provider instances based on configuration.
    """

    @staticmethod
    def create_provider(provider: LLMProviderType, **kwargs) -> LLMProvider:
        """
        Create an LLM provider instance.
        """
        match provider:
            case LLMProviderType.GROQ:
                return GroqProvider(**kwargs)
