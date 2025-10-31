"""
Tests for the base agent class.
"""

import pytest

from app.agents.base import AgentError, AgentProcessingError, AgentValidationError, BaseAgent
from app.services.llm.base import LLMError, LLMProvider


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing."""

    def __init__(self, response="Mock LLM response", should_fail=False, fail_with=LLMError):
        self.response = response
        self.should_fail = should_fail
        self.fail_with = fail_with
        self.generate_calls = []
        self.stream_calls = []

    async def generate(self, messages, max_tokens=None, temperature=None, **kwargs):
        self.generate_calls.append(
            {
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "kwargs": kwargs,
            }
        )

        if self.should_fail:
            raise self.fail_with("Mock LLM error")

        return self.response

    async def generate_stream(self, messages, max_tokens=None, temperature=None, **kwargs):
        self.stream_calls.append(
            {
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "kwargs": kwargs,
            }
        )

        if self.should_fail:
            raise self.fail_with("Mock LLM error")

        for chunk in ["Mock ", "streaming ", "response"]:
            yield chunk


class ConcreteTestAgent(BaseAgent):
    """Concrete test implementation of BaseAgent."""

    def __init__(self, llm_provider, return_value="Test result", should_fail=False):
        super().__init__(llm_provider)
        self.return_value = return_value
        self.should_fail = should_fail
        self.run_calls = []

    async def run(self, *args, **kwargs):
        self.run_calls.append({"args": args, "kwargs": kwargs})

        if self.should_fail:
            raise AgentProcessingError("Test agent failed")

        return self.return_value


class TestBaseAgent:
    """Test the BaseAgent abstract class."""

    @pytest.fixture
    def mock_llm(self):
        return MockLLMProvider()

    @pytest.fixture
    def test_agent(self, mock_llm):
        return ConcreteTestAgent(mock_llm)

    def test_agent_initialization(self, mock_llm):
        """Test that agent is properly initialized with LLM provider."""
        agent = ConcreteTestAgent(mock_llm)
        assert agent.llm == mock_llm

    @pytest.mark.asyncio
    async def test_agent_run_method(self, test_agent):
        """Test that the run method can be called and returns expected result."""
        result = await test_agent.run("test_arg", test_kwarg="test_value")
        assert result == "Test result"
        assert len(test_agent.run_calls) == 1
        assert test_agent.run_calls[0]["args"] == ("test_arg",)
        assert test_agent.run_calls[0]["kwargs"] == {"test_kwarg": "test_value"}

    @pytest.mark.asyncio
    async def test_agent_run_failure(self, mock_llm):
        """Test that agent failures are properly handled."""
        failing_agent = ConcreteTestAgent(mock_llm, should_fail=True)

        with pytest.raises(AgentProcessingError, match="Test agent failed"):
            await failing_agent.run()

    def test_build_system_prompt_default(self, test_agent):
        """Test the default system prompt."""
        prompt = test_agent._build_system_prompt()
        assert prompt == "You are a helpful AI assistant."

    @pytest.mark.asyncio
    async def test_generate_response_basic(self, test_agent):
        """Test basic response generation."""
        response = await test_agent._generate_response("Test user prompt")

        assert response == "Mock LLM response"
        assert len(test_agent.llm.generate_calls) == 1

        call = test_agent.llm.generate_calls[0]
        assert len(call["messages"]) == 2
        assert call["messages"][0]["role"] == "system"
        assert call["messages"][0]["content"] == "You are a helpful AI assistant."
        assert call["messages"][1]["role"] == "user"
        assert call["messages"][1]["content"] == "Test user prompt"

    @pytest.mark.asyncio
    async def test_generate_response_with_custom_system_prompt(self, test_agent):
        """Test response generation with custom system prompt."""
        custom_system = "You are a specialized assistant."
        response = await test_agent._generate_response(
            "Test user prompt", system_prompt=custom_system
        )

        assert response == "Mock LLM response"
        call = test_agent.llm.generate_calls[0]
        assert call["messages"][0]["content"] == custom_system

    @pytest.mark.asyncio
    async def test_generate_response_with_generation_kwargs(self, test_agent):
        """Test response generation with additional parameters."""
        response = await test_agent._generate_response(
            "Test user prompt", max_tokens=100, temperature=0.7, custom_param="test_value"
        )

        assert response == "Mock LLM response"
        call = test_agent.llm.generate_calls[0]
        assert call["max_tokens"] == 100
        assert call["temperature"] == 0.7
        assert call["kwargs"]["custom_param"] == "test_value"

    @pytest.mark.asyncio
    async def test_generate_response_llm_error(self, mock_llm):
        """Test handling of LLM errors during generation."""
        failing_llm = MockLLMProvider(should_fail=True)
        agent = ConcreteTestAgent(failing_llm)

        with pytest.raises(LLMError, match="Mock LLM error"):
            await agent._generate_response("Test prompt")


class TestAgentExceptions:
    """Test agent exception hierarchy."""

    def test_agent_error_inheritance(self):
        """Test that all agent errors inherit from AgentError."""
        assert issubclass(AgentValidationError, AgentError)
        assert issubclass(AgentProcessingError, AgentError)

    def test_exception_instantiation(self):
        """Test that exceptions can be instantiated with messages."""
        error = AgentError("Test error")
        assert str(error) == "Test error"

        validation_error = AgentValidationError("Validation failed")
        assert str(validation_error) == "Validation failed"

        processing_error = AgentProcessingError("Processing failed")
        assert str(processing_error) == "Processing failed"


class TestAgentIntegration:
    """Integration tests for agent functionality."""

    @pytest.fixture
    def multi_response_llm(self):
        """LLM that tracks multiple calls."""
        return MockLLMProvider(response="Response from LLM")

    @pytest.fixture
    def agent_with_tracking(self, multi_response_llm):
        return ConcreteTestAgent(multi_response_llm)

    @pytest.mark.asyncio
    async def test_multiple_generate_calls(self, agent_with_tracking):
        """Test that multiple generation calls work correctly."""
        # First call
        response1 = await agent_with_tracking._generate_response("First prompt")
        assert response1 == "Response from LLM"

        # Second call with different parameters
        response2 = await agent_with_tracking._generate_response(
            "Second prompt", system_prompt="Custom system", max_tokens=50
        )
        assert response2 == "Response from LLM"

        # Verify both calls were tracked
        assert len(agent_with_tracking.llm.generate_calls) == 2

        # Verify first call
        call1 = agent_with_tracking.llm.generate_calls[0]
        assert call1["messages"][1]["content"] == "First prompt"
        assert call1["max_tokens"] is None

        # Verify second call
        call2 = agent_with_tracking.llm.generate_calls[1]
        assert call2["messages"][0]["content"] == "Custom system"
        assert call2["messages"][1]["content"] == "Second prompt"
        assert call2["max_tokens"] == 50

    @pytest.mark.asyncio
    async def test_agent_with_different_llm_responses(self):
        """Test agent behavior with different LLM responses."""
        # Test with empty response
        empty_llm = MockLLMProvider(response="")
        empty_agent = ConcreteTestAgent(empty_llm)
        response = await empty_agent._generate_response("Test")
        assert response == ""

        # Test with long response
        long_response = "This is a very long response " * 100
        long_llm = MockLLMProvider(response=long_response)
        long_agent = ConcreteTestAgent(long_llm)
        response = await long_agent._generate_response("Test")
        assert response == long_response

        # Test with special characters
        special_response = "Response with émojis 🎉 and símböls!"
        special_llm = MockLLMProvider(response=special_response)
        special_agent = ConcreteTestAgent(special_llm)
        response = await special_agent._generate_response("Test")
        assert response == special_response
