"""
Groq provider implementation.
"""

from collections.abc import AsyncGenerator
from typing import Any, cast

from groq import AsyncGroq
from groq.types.chat import ChatCompletionMessageParam

from ..base import LLMConnectionError, LLMProvider, LLMRateLimitError, LLMValidationError


class GroqProvider(LLMProvider):
    """
    Groq LLM provider using the Chat Completions API.

    Implements the LLMProvider interface for Groq's fast inference models.
    Groq uses an OpenAI-compatible API format.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "llama-3.3-70b-versatile",
        base_url: str | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize Groq provider.

        Args:
            api_key: Groq API key
            model: Groq model name (e.g., "llama-3.3-70b-versatile", "mixtral-8x7b-32768")
            base_url: Optional custom API base URL
            **kwargs: Additional configuration options
        """
        self.api_key = api_key
        self.model = model
        self.base_url = base_url or "https://api.groq.com/openai/v1"

        # Initialize Groq async client
        # Note: AsyncGroq automatically appends /openai/v1 to base_url, so we use the root URL
        client_base_url = base_url or "https://api.groq.com"
        self.client = AsyncGroq(api_key=api_key, base_url=client_base_url, **kwargs)

    async def generate(
        self,
        messages: list[dict[str, str]],
        max_tokens: int | None = None,
        temperature: float | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Generate text response using Groq Chat Completions API.

        Args:
            messages: List of message dictionaries
            max_tokens: Maximum tokens to generate (default: 1000)
            temperature: Sampling temperature (default: 0.7)
            **kwargs: Additional Groq-specific parameters

        Returns:
            Generated text response
        """
        # Set defaults
        max_tokens = max_tokens or 1000
        temperature = temperature or 0.7

        try:
            # Call Groq API - cast messages to proper type for Groq client
            groq_messages = cast(list[ChatCompletionMessageParam], messages)
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=groq_messages,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs,
            )

            return response.choices[0].message.content or ""

        except Exception as e:
            # Handle specific Groq exceptions
            error_str = str(e).lower()
            if "rate_limit" in error_str or "429" in error_str:
                raise LLMRateLimitError(f"Groq rate limit exceeded: {e}") from e
            elif (
                "validation" in error_str
                or "invalid" in error_str
                or "400" in error_str
                or "bad request" in error_str
            ):
                raise LLMValidationError(f"Groq validation error: {e}") from e
            elif "unauthorized" in error_str or "401" in error_str or "api key" in error_str:
                raise LLMValidationError(f"Groq authentication error: {e}") from e
            elif "connection" in error_str or "timeout" in error_str or "network" in error_str:
                raise LLMConnectionError(f"Groq connection error: {e}") from e
            else:
                raise LLMConnectionError(f"Groq API error: {e}") from e

    def generate_stream(
        self,
        messages: list[dict[str, str]],
        max_tokens: int | None = None,
        temperature: float | None = None,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """
        Generate streaming text response using Groq Chat Completions API.

        Args:
            messages: List of message dictionaries
            max_tokens: Maximum tokens to generate (default: 1000)
            temperature: Sampling temperature (default: 0.7)
            **kwargs: Additional Groq-specific parameters

        Yields:
            Chunks of generated text
        """
        return self._stream_generator(messages, max_tokens, temperature, **kwargs)

    async def _stream_generator(
        self,
        messages: list[dict[str, str]],
        max_tokens: int | None = None,
        temperature: float | None = None,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """Internal async generator for streaming."""
        # Set defaults
        max_tokens = max_tokens or 1000
        temperature = temperature or 0.7

        try:
            # Call Groq streaming API - cast messages to proper type for Groq client
            groq_messages = cast(list[ChatCompletionMessageParam], messages)
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=groq_messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True,
                **kwargs,
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            # Handle specific Groq exceptions
            error_str = str(e).lower()
            if "rate_limit" in error_str or "429" in error_str:
                raise LLMRateLimitError(f"Groq rate limit exceeded: {e}") from e
            elif (
                "validation" in error_str
                or "invalid" in error_str
                or "400" in error_str
                or "bad request" in error_str
            ):
                raise LLMValidationError(f"Groq validation error: {e}") from e
            elif "unauthorized" in error_str or "401" in error_str or "api key" in error_str:
                raise LLMValidationError(f"Groq authentication error: {e}") from e
            elif "connection" in error_str or "timeout" in error_str or "network" in error_str:
                raise LLMConnectionError(f"Groq connection error: {e}") from e
            else:
                raise LLMConnectionError(f"Groq API error: {e}") from e
