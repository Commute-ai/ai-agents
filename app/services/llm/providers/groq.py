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
        self._api_key = api_key
        self._model = model
        self._client = AsyncGroq(api_key=api_key, **kwargs)

    def _should_use_json_format(self, messages: list[dict[str, str]]) -> bool:
        """
        Determine if JSON format should be used based on message content.

        Groq requires that messages contain the word "json" when using json_object format.
        This method checks if any message mentions JSON/json to decide if JSON format is appropriate.

        Args:
            messages: List of message dictionaries

        Returns:
            True if JSON format should be used, False otherwise
        """
        for message in messages:
            content = message.get("content", "").lower()
            if "json" in content:
                return True
        return False

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

        # Determine if JSON format should be used based on message content
        # Groq requires the word "json" in messages when using json_object format
        use_json_format = self._should_use_json_format(messages)

        try:
            # Call Groq API - cast messages to proper type for Groq client
            groq_messages = cast(list[ChatCompletionMessageParam], messages)

            # Prepare request parameters
            request_params = {
                "model": self._model,
                "messages": groq_messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                **kwargs,
            }

            # Only add response_format if JSON is requested and message content supports it
            if use_json_format:
                request_params["response_format"] = {"type": "json_object"}

            response = await self._client.chat.completions.create(**request_params)

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
            stream = await self._client.chat.completions.create(
                model=self._model,
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
