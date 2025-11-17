"""
Tests for LLM service providers.
"""

from unittest.mock import patch

import pytest

from app.llm.base import (
    LLMConnectionError,
    LLMError,
    LLMProvider,
    LLMRateLimitError,
    LLMValidationError,
)
from app.llm.factory import LLMProviderFactory


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing."""

    def __init__(self, **kwargs):
        self.config = kwargs
        self.should_fail = kwargs.get("should_fail", False)
        self.fail_with = kwargs.get("fail_with", LLMError)
        self.response = kwargs.get("response", "Mock response")

    async def generate(self, messages, max_tokens=None, temperature=None, **kwargs):
        if self.should_fail:
            raise self.fail_with("Mock error")
        return self.response

    async def generate_stream(self, messages, max_tokens=None, temperature=None, **kwargs):
        if self.should_fail:
            raise self.fail_with("Mock error")
        for chunk in ["Mock ", "streaming ", "response"]:
            yield chunk


class TestLLMProvider:
    """Test the base LLM provider interface."""

    @pytest.fixture
    def mock_provider(self):
        return MockLLMProvider()

    @pytest.fixture
    def failing_provider(self):
        return MockLLMProvider(should_fail=True)

    @pytest.mark.asyncio
    async def test_generate_success(self, mock_provider):
        """Test successful text generation."""
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"},
        ]

        response = await mock_provider.generate(messages)
        assert response == "Mock response"

    @pytest.mark.asyncio
    async def test_generate_with_parameters(self, mock_provider):
        """Test generation with additional parameters."""
        messages = [{"role": "user", "content": "Test"}]

        response = await mock_provider.generate(messages, max_tokens=100, temperature=0.7)
        assert response == "Mock response"

    @pytest.mark.asyncio
    async def test_generate_failure(self, failing_provider):
        """Test handling of generation failures."""
        messages = [{"role": "user", "content": "Test"}]

        with pytest.raises(LLMError, match="Mock error"):
            await failing_provider.generate(messages)

    @pytest.mark.asyncio
    async def test_generate_stream_success(self, mock_provider):
        """Test successful streaming generation."""
        messages = [{"role": "user", "content": "Test"}]

        chunks = []
        async for chunk in mock_provider.generate_stream(messages):
            chunks.append(chunk)

        assert chunks == ["Mock ", "streaming ", "response"]

    @pytest.mark.asyncio
    async def test_generate_stream_failure(self, failing_provider):
        """Test handling of streaming failures."""
        messages = [{"role": "user", "content": "Test"}]

        with pytest.raises(LLMError, match="Mock error"):
            async for _ in failing_provider.generate_stream(messages):
                pass


class TestLLMExceptions:
    """Test LLM exception hierarchy."""

    def test_llm_error_inheritance(self):
        """Test that all LLM errors inherit from LLMError."""
        assert issubclass(LLMConnectionError, LLMError)
        assert issubclass(LLMRateLimitError, LLMError)
        assert issubclass(LLMValidationError, LLMError)

    def test_exception_instantiation(self):
        """Test that exceptions can be instantiated with messages."""
        error = LLMError("Test error")
        assert str(error) == "Test error"

        conn_error = LLMConnectionError("Connection failed")
        assert str(conn_error) == "Connection failed"

        rate_error = LLMRateLimitError("Rate limit exceeded")
        assert str(rate_error) == "Rate limit exceeded"

        validation_error = LLMValidationError("Invalid input")
        assert str(validation_error) == "Invalid input"


class TestLLMProviderFactory:
    """Test the LLM provider factory."""

    def test_factory_exists(self):
        """Test that the factory class exists."""
        assert hasattr(LLMProviderFactory, "create_provider")

    @patch("app.llm.factory.LLMProviderFactory.create_provider")
    def test_factory_can_be_mocked(self, mock_create):
        """Test that factory can be mocked for testing."""
        mock_provider = MockLLMProvider()
        mock_create.return_value = mock_provider

        result = LLMProviderFactory.create_provider("test", api_key="test")
        assert result == mock_provider
        mock_create.assert_called_once_with("test", api_key="test")


@pytest.mark.asyncio
class TestLLMProviderIntegration:
    """Integration tests for LLM providers."""

    @pytest.fixture
    def custom_response_provider(self):
        return MockLLMProvider(response="Custom test response")

    async def test_different_message_formats(self, custom_response_provider):
        """Test handling of different message formats."""
        # Test with system and user messages
        messages1 = [
            {"role": "system", "content": "You are an assistant."},
            {"role": "user", "content": "Hello"},
        ]

        response1 = await custom_response_provider.generate(messages1)
        assert response1 == "Custom test response"

        # Test with user message only
        messages2 = [{"role": "user", "content": "Hello"}]

        response2 = await custom_response_provider.generate(messages2)
        assert response2 == "Custom test response"

    async def test_parameter_combinations(self, custom_response_provider):
        """Test various parameter combinations."""
        messages = [{"role": "user", "content": "Test"}]

        # Test with max_tokens only
        response1 = await custom_response_provider.generate(messages, max_tokens=50)
        assert response1 == "Custom test response"

        # Test with temperature only
        response2 = await custom_response_provider.generate(messages, temperature=0.8)
        assert response2 == "Custom test response"

        # Test with both parameters
        response3 = await custom_response_provider.generate(
            messages, max_tokens=100, temperature=0.5
        )
        assert response3 == "Custom test response"

    async def test_error_propagation(self):
        """Test that different types of errors are properly propagated."""
        # Test connection error
        conn_provider = MockLLMProvider(should_fail=True, fail_with=LLMConnectionError)
        with pytest.raises(LLMConnectionError):
            await conn_provider.generate([{"role": "user", "content": "test"}])

        # Test rate limit error
        rate_provider = MockLLMProvider(should_fail=True, fail_with=LLMRateLimitError)
        with pytest.raises(LLMRateLimitError):
            await rate_provider.generate([{"role": "user", "content": "test"}])

        # Test validation error
        validation_provider = MockLLMProvider(should_fail=True, fail_with=LLMValidationError)
        with pytest.raises(LLMValidationError):
            await validation_provider.generate([{"role": "user", "content": "test"}])
