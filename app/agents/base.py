"""
Base agent class for AI-powered tasks.
"""

from abc import ABC, abstractmethod
from typing import Any

from app.services.llm.base import LLMProvider


class BaseAgent(ABC):
    """
    Abstract base class for AI agents.

    Agents encapsulate specific AI-powered tasks and handle prompt engineering,
    LLM interaction, and response processing.
    """

    def __init__(self, llm_provider: LLMProvider) -> None:
        """
        Initialize the agent with an LLM provider.

        Args:
            llm_provider: LLM provider instance for text generation
        """
        self.llm = llm_provider

    @abstractmethod
    async def run(self, *args: Any, **kwargs: Any) -> Any:
        """
        Execute the agent's main task.

        This method should be implemented by subclasses to define the specific
        task logic, including prompt construction, LLM interaction, and
        response processing.

        Args:
            Task-specific input parameters
        Returns:
            Task-specific output
        """
        pass

    def _build_system_prompt(self) -> str:
        """
        Build the system prompt that defines the agent's role and behavior.

        Returns:
            System prompt string
        """
        return "You are a helpful AI assistant."

    async def _generate_response(
        self, user_prompt: str, system_prompt: str | None = None, **generation_kwargs: Any
    ) -> str:
        """
        Generate a response using the LLM provider.

        Args:
            user_prompt: The user prompt/query
            system_prompt: Optional system prompt (uses default if not provided)
            **generation_kwargs: Additional parameters for LLM generation

        Returns:
            Generated response text
        """
        system_prompt = system_prompt or self._build_system_prompt()

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        return await self.llm.generate(messages, **generation_kwargs)


class AgentError(Exception):
    """Base exception for agent errors."""

    pass


class AgentValidationError(AgentError):
    """Raised when agent input validation fails."""

    pass


class AgentProcessingError(AgentError):
    """Raised when agent processing fails."""

    pass
