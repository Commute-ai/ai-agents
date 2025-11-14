from collections.abc import Generator
from datetime import datetime

from fastapi.testclient import TestClient
import pytest

from app.llm.base import LLMProvider
from app.main import app
from app.schemas.geo import Coordinates
from app.schemas.itinerary import ItineraryInsight, LegInsight
from app.schemas.weather import WeatherCondition


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing."""

    def __init__(self, response='{"itinerary_insights": []}', should_fail=False, fail_with=None):
        self.response = response
        self.should_fail = should_fail
        self.fail_with = fail_with or Exception
        self.generate_calls = []

    async def generate(self, messages, max_tokens=None, temperature=None, **kwargs):
        # Record the call for assertion purposes
        call_info = {
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            **kwargs,
        }
        self.generate_calls.append(call_info)

        if self.should_fail:
            raise self.fail_with("Mock LLM error")
        return self.response

    async def generate_stream(self, messages, max_tokens=None, temperature=None, **kwargs):
        if self.should_fail:
            raise Exception("Mock LLM error")
        for chunk in ["Mock ", "streaming ", "response"]:
            yield chunk


class MockInsightService:
    """Mock insight service for testing."""

    def __init__(self, should_fail=False):
        self.should_fail = should_fail

    async def generate_insights(self, itineraries, user_preferences=None):
        if self.should_fail:
            raise Exception("Mock insight service error")

        # Validate at least one itinerary is required (same as real service)
        if len(itineraries) == 0:
            raise ValueError("At least one itinerary is required")

        # Return mock insights for each itinerary
        insights = []
        for itinerary in itineraries:
            # Create mock leg insights for each leg
            leg_insights = [
                LegInsight(ai_insight=f"Mock insight for leg {i + 1}")
                for i, _ in enumerate(itinerary.legs)
            ]

            insight = ItineraryInsight(
                ai_insight="Mock overall itinerary insight", leg_insights=leg_insights
            )
            insights.append(insight)

        return insights


class MockWeatherService:
    """Mock weather service for testing."""

    def __init__(self, should_fail=False):
        self.should_fail = should_fail

    async def get_current_weather(self, coordinates: Coordinates):
        if self.should_fail:
            raise Exception("Mock weather service error")

        return WeatherCondition(
            temperature=10.0,
            description="Sunny",
            humidity=50,
            wind_speed=5.0,
            precipitation=0.0,
            timestamp=datetime.now(),
        )


@pytest.fixture(scope="function")
def client() -> Generator[TestClient, None, None]:
    """
    Create a fresh test client for each test function.
    This ensures test isolation and prevents state leakage between tests.
    """
    # Override the insight service dependency to avoid requiring real API keys
    from app.dependencies import get_insight_service

    mock_service = MockInsightService()
    app.dependency_overrides[get_insight_service] = lambda: mock_service

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
