from collections.abc import Generator

from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.services.llm.base import LLMProvider


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing."""

    def __init__(self, response="Mock AI response", should_fail=False):
        self.response = response
        self.should_fail = should_fail

    async def generate(self, messages, max_tokens=None, temperature=None, **kwargs):
        if self.should_fail:
            raise Exception("Mock LLM error")
        return self.response

    async def generate_stream(self, messages, max_tokens=None, temperature=None, **kwargs):
        if self.should_fail:
            raise Exception("Mock LLM error")
        for chunk in ["Mock ", "streaming ", "response"]:
            yield chunk


@pytest.fixture(scope="function")
def client() -> Generator[TestClient, None, None]:
    """
    Create a fresh test client for each test function.
    This ensures test isolation and prevents state leakage between tests.
    """
    # Override the LLM provider dependency to avoid requiring real API keys
    from app.dependencies import get_llm_provider

    mock_provider = MockLLMProvider()
    app.dependency_overrides[get_llm_provider] = lambda: mock_provider

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        # Clean up dependency override
        app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def anyio_backend():
    """
    Configure pytest-asyncio to use asyncio backend for async tests.
    Required for FastAPI async route testing.
    """
    return "asyncio"
