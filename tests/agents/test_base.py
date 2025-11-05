"""
Tests for the base agent class.
"""

from unittest.mock import MagicMock, patch

from pydantic import BaseModel
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


class InputModel(BaseModel):
    """Test input model."""

    message: str


class OutputModel(BaseModel):
    """Test output model."""

    result: str


class ConcreteTestAgent(BaseAgent):
    """Concrete test implementation of BaseAgent."""

    input_model = InputModel
    output_model = OutputModel

    def __init__(self, llm_provider):
        super().__init__(llm_provider)


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
        assert agent.llm_provider == mock_llm
        assert agent.input_model == InputModel
        assert agent.output_model == OutputModel

    @pytest.mark.asyncio
    async def test_agent_execute_method(self, test_agent):
        """Test that the execute method can be called and returns expected result."""

        test_agent.llm_provider.response = '{"result": "Test result"}'
        input_data = InputModel(message="test message")

        # Mock template loading to avoid file system dependencies
        with patch.object(test_agent, "_load_template") as mock_load:
            from unittest.mock import MagicMock

            mock_template = MagicMock()
            mock_template.render.return_value = "Mocked template content"
            mock_load.return_value = mock_template

            result = await test_agent.execute(input_data)
            assert isinstance(result, OutputModel)
            assert result.result == "Test result"

    @pytest.mark.asyncio
    async def test_agent_execute_validation_error(self, test_agent):
        """Test that input validation works correctly."""
        # This should raise a validation error since we're passing wrong input type
        with pytest.raises(AgentValidationError):
            await test_agent.execute("not a pydantic model")

    @pytest.mark.asyncio
    async def test_agent_execute_llm_error(self, mock_llm):
        """Test that LLM errors are properly propagated."""
        mock_llm.should_fail = True
        agent = ConcreteTestAgent(mock_llm)
        input_data = InputModel(message="test message")

        # Mock template loading
        with patch.object(agent, "_load_template") as mock_load:
            mock_template = MagicMock()
            mock_template.render.return_value = "Mocked template content"
            mock_load.return_value = mock_template

            with pytest.raises(LLMError):
                await agent.execute(input_data)

    @pytest.mark.asyncio
    async def test_agent_execute_json_parsing_error(self, test_agent):
        """Test that invalid JSON responses are handled."""
        test_agent.llm_provider.response = "invalid json"
        input_data = InputModel(message="test message")

        # Mock template loading
        with patch.object(test_agent, "_load_template") as mock_load:
            mock_template = MagicMock()
            mock_template.render.return_value = "Mocked template content"
            mock_load.return_value = mock_template

            with pytest.raises(AgentProcessingError):
                await test_agent.execute(input_data)

    @pytest.mark.asyncio
    async def test_agent_execute_with_markdown_json(self, test_agent):
        """Test that JSON wrapped in markdown code blocks is properly parsed."""
        # Response with JSON wrapped in markdown code blocks
        test_agent.llm_provider.response = '```json\n{"result": "Markdown wrapped result"}\n```'
        input_data = InputModel(message="test message")

        # Mock template loading
        with patch.object(test_agent, "_load_template") as mock_load:
            mock_template = MagicMock()
            mock_template.render.return_value = "Mocked template content"
            mock_load.return_value = mock_template

            result = await test_agent.execute(input_data)
            assert isinstance(result, OutputModel)
            assert result.result == "Markdown wrapped result"

    @pytest.mark.asyncio
    async def test_agent_execute_with_plain_markdown_blocks(self, test_agent):
        """Test that plain markdown blocks (without json specifier) are handled."""
        # Response with JSON wrapped in plain markdown code blocks
        test_agent.llm_provider.response = '```\n{"result": "Plain markdown result"}\n```'
        input_data = InputModel(message="test message")

        # Mock template loading
        with patch.object(test_agent, "_load_template") as mock_load:
            mock_template = MagicMock()
            mock_template.render.return_value = "Mocked template content"
            mock_load.return_value = mock_template

            result = await test_agent.execute(input_data)
            assert isinstance(result, OutputModel)
            assert result.result == "Plain markdown result"

    @pytest.mark.asyncio
    async def test_agent_execute_calls_llm_correctly(self, test_agent):
        """Test that the execute method calls the LLM with correct parameters."""
        test_agent.llm_provider.response = '{"result": "Test result"}'
        input_data = InputModel(message="test message")

        # Mock template loading
        with patch.object(test_agent, "_load_template") as mock_load:
            mock_template = MagicMock()
            mock_template.render.return_value = "Mocked template content"
            mock_load.return_value = mock_template

            await test_agent.execute(input_data)

            # Check that LLM was called
            assert len(test_agent.llm_provider.generate_calls) == 1
            call = test_agent.llm_provider.generate_calls[0]

            # Check that messages were passed correctly
            assert "messages" in call
            assert len(call["messages"]) == 2
            assert call["messages"][0]["role"] == "system"
            assert call["messages"][1]["role"] == "user"

    def test_extract_json_from_response_plain_json(self, test_agent):
        """Test extracting JSON from plain JSON response."""
        response = '{"result": "plain json"}'
        extracted = test_agent._extract_json_from_response(response)
        assert extracted == '{"result": "plain json"}'

    def test_extract_json_from_response_markdown_json(self, test_agent):
        """Test extracting JSON from markdown ```json code blocks."""
        response = '```json\n{"result": "markdown json"}\n```'
        extracted = test_agent._extract_json_from_response(response)
        assert extracted == '{"result": "markdown json"}'

    def test_extract_json_from_response_plain_markdown(self, test_agent):
        """Test extracting JSON from plain ``` code blocks."""
        response = '```\n{"result": "plain markdown"}\n```'
        extracted = test_agent._extract_json_from_response(response)
        assert extracted == '{"result": "plain markdown"}'

    def test_extract_json_from_response_with_whitespace(self, test_agent):
        """Test extracting JSON with extra whitespace."""
        response = '  \n```json\n  {"result": "whitespace"}  \n```\n  '
        extracted = test_agent._extract_json_from_response(response)
        assert extracted == '{"result": "whitespace"}'


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
    def mock_llm(self):
        return MockLLMProvider()

    @pytest.fixture
    def test_agent(self, mock_llm):
        return ConcreteTestAgent(mock_llm)

    @pytest.mark.asyncio
    async def test_multiple_execute_calls(self, test_agent):
        """Test that multiple executions work correctly."""
        test_agent.llm_provider.response = '{"result": "Response"}'
        input_data = InputModel(message="test")

        # Mock template loading
        with patch.object(test_agent, "_load_template") as mock_load:
            mock_template = MagicMock()
            mock_template.render.return_value = "Mocked template content"
            mock_load.return_value = mock_template

            # Make multiple calls
            result1 = await test_agent.execute(input_data)
            result2 = await test_agent.execute(input_data)

            assert result1.result == "Response"
            assert result2.result == "Response"
            assert len(test_agent.llm_provider.generate_calls) == 2

    @pytest.mark.asyncio
    async def test_agent_with_different_llm_responses(self, mock_llm):
        """Test agent with different LLM responses."""
        agent = ConcreteTestAgent(mock_llm)
        input_data = InputModel(message="test")

        # Mock template loading
        with patch.object(agent, "_load_template") as mock_load:
            mock_template = MagicMock()
            mock_template.render.return_value = "Mocked template content"
            mock_load.return_value = mock_template

            # First call
            mock_llm.response = '{"result": "First response"}'
            result1 = await agent.execute(input_data)
            assert result1.result == "First response"

            # Second call with different response
            mock_llm.response = '{"result": "Second response"}'
            result2 = await agent.execute(input_data)
            assert result2.result == "Second response"
