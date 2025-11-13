"""
Integration tests for the Groq provider.

These tests require a valid GROQ_API_KEY environment variable.
They will be skipped if the API key is not available.
"""

import os

import pytest

from app.llm.base import LLMError
from app.llm.providers.groq import GroqProvider


@pytest.mark.skipif(
    not os.getenv("GROQ_API_KEY"), reason="GROQ_API_KEY environment variable not set"
)
class TestGroqIntegration:
    """Integration tests for Groq provider."""

    @pytest.fixture
    def groq_provider(self):
        """Create a Groq provider with real API key."""
        from unittest.mock import patch

        with patch("app.llm.providers.groq.settings") as mock_settings:
            mock_settings.GROQ_API_KEY = os.getenv("GROQ_API_KEY")
            mock_settings.GROQ_MODEL = "llama-3.3-70b-versatile"
            return GroqProvider()

    @pytest.mark.asyncio
    async def test_groq_generate_basic(self, groq_provider):
        """Test basic text generation with Groq."""
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say hello in exactly 3 words."},
        ]

        response = await groq_provider.generate(messages, max_tokens=10, temperature=0.1)

        assert isinstance(response, str)
        assert len(response) > 0
        # Groq should respond very quickly
        print(f"Groq response: {response}")

    @pytest.mark.asyncio
    async def test_groq_generate_with_parameters(self, groq_provider):
        """Test generation with specific parameters."""
        messages = [{"role": "user", "content": "Explain quantum computing in one sentence."}]

        response = await groq_provider.generate(messages, max_tokens=50, temperature=0.5)

        assert isinstance(response, str)
        assert len(response) > 10  # Should be a meaningful response
        print(f"Groq quantum explanation: {response}")

    @pytest.mark.asyncio
    async def test_groq_streaming(self, groq_provider):
        """Test streaming response from Groq."""
        messages = [{"role": "user", "content": "Count from 1 to 5."}]

        chunks = []
        async for chunk in groq_provider.generate_stream(messages, max_tokens=20):
            chunks.append(chunk)

        full_response = "".join(chunks)
        assert len(chunks) > 1  # Should stream in multiple chunks
        assert len(full_response) > 0
        print(f"Groq streaming response: {full_response}")

    @pytest.mark.asyncio
    async def test_groq_error_handling(self):
        """Test error handling with invalid API key."""
        from unittest.mock import patch

        with patch("app.llm.providers.groq.settings") as mock_settings:
            mock_settings.GROQ_API_KEY = "invalid-key"
            mock_settings.GROQ_MODEL = "llama-3.3-70b-versatile"
            provider = GroqProvider()

            messages = [{"role": "user", "content": "Hello"}]

            with pytest.raises(LLMError):
                await provider.generate(messages)


@pytest.mark.asyncio
async def test_groq_config_integration():
    """Test creating Groq provider from configuration."""
    from unittest.mock import patch

    from app.llm.factory import LLMProviderFactory, LLMProviderType

    # Mock the settings to use Groq
    with patch("app.llm.providers.groq.settings") as mock_settings:
        mock_settings.GROQ_API_KEY = "test-api-key"
        mock_settings.GROQ_MODEL = "llama-3.3-70b-versatile"

        # Mock the Groq client's generate method directly
        with patch("app.llm.providers.groq.GroqProvider.generate") as mock_generate:
            mock_generate.return_value = "Hello! How can I help you?"

            provider = LLMProviderFactory.create_provider(LLMProviderType.GROQ)

            # Test that it can generate a response
            messages = [{"role": "user", "content": "Hello!"}]
            response = await provider.generate(messages, max_tokens=10)

            assert isinstance(response, str)
            assert response == "Hello! How can I help you?"


def test_groq_provider_without_api_key():
    """Test that Groq provider can be instantiated without real API key for testing."""
    from unittest.mock import patch

    with patch("app.llm.providers.groq.settings") as mock_settings:
        mock_settings.GROQ_API_KEY = "test-key"
        mock_settings.GROQ_MODEL = "llama-3.3-70b-versatile"
        provider = GroqProvider()

        assert provider._api_key == "test-key"
        assert provider._model == "llama-3.3-70b-versatile"
        assert provider._client is not None
