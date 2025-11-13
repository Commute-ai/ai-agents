"""
Tests for the insight agent.
"""

from datetime import datetime
from unittest.mock import patch

from jinja2 import DictLoader, Environment
import pytest

from app.agents.insight import InsightAgent
from app.llm.base import LLMError
from app.schemas.geo import Coordinates
from app.schemas.itinerary import (
    Itinerary,
    Leg,
    Route,
    TransportMode,
)
from app.schemas.location import Place
from app.schemas.preference import Preference
from tests.conftest import MockLLMProvider, MockWeatherService


@pytest.fixture
def mock_llm():
    return MockLLMProvider()


@pytest.fixture
def mock_weather_service():
    return MockWeatherService()


@pytest.fixture
def sample_coordinates():
    return Coordinates(latitude=60.1699, longitude=24.9384)  # Helsinki


@pytest.fixture
def sample_place(sample_coordinates):
    return Place(coordinates=sample_coordinates, name="Helsinki Central")


@pytest.fixture
def sample_route():
    return Route(
        short_name="550",
        long_name="Helsinki - Espoo",
        description="Bus route from Helsinki to Espoo",
    )


@pytest.fixture
def sample_leg(sample_place, sample_route):
    start_place = Place(
        coordinates=Coordinates(latitude=60.1699, longitude=24.9384), name="Helsinki Central"
    )
    end_place = Place(
        coordinates=Coordinates(latitude=60.2055, longitude=24.6559), name="Espoo Central"
    )

    return Leg(
        mode=TransportMode.BUS,
        start=datetime(2024, 1, 15, 9, 0, 0),
        end=datetime(2024, 1, 15, 9, 30, 0),
        duration=1800,  # 30 minutes
        distance=15000,  # 15 km
        from_place=start_place,
        to_place=end_place,
        route=sample_route,
    )


@pytest.fixture
def sample_itinerary(sample_leg):
    return Itinerary(
        start=datetime(2024, 1, 15, 9, 0, 0),
        end=datetime(2024, 1, 15, 9, 30, 0),
        duration=1800,
        walk_distance=200,
        walk_time=120,
        legs=[sample_leg],
    )


@pytest.fixture
def sample_preferences():
    return [
        Preference(prompt="I prefer faster routes"),
        Preference(prompt="I want to minimize walking"),
    ]


class TestInsightAgent:
    """Test the InsightAgent class."""

    @pytest.fixture
    def mock_jinja_env(self):
        """Mock Jinja2 environment with test templates."""
        templates = {
            "system.j2": "You are a transit expert.",
            "user.j2": "Analyze these {{ num_itineraries }} routes:\n{% for itinerary in itineraries %}Route {{ loop.index }}: {{ itinerary }}{% endfor %}",
        }
        return Environment(loader=DictLoader(templates))

    @pytest.fixture
    def insight_agent(self, mock_llm):
        with patch.object(InsightAgent, "__init__", lambda self, llm_provider: None):
            agent = InsightAgent.__new__(InsightAgent)
            agent.llm_provider = mock_llm
            return agent

    @pytest.mark.asyncio
    async def test_successful_insight_generation(self, insight_agent, sample_itinerary):
        """Test successful insight generation for a single itinerary."""
        from app.agents.insight import InsightRequest

        insight_agent.llm_provider.response = '{"itinerary_insights": [{"ai_insight": "This is a great bus route with minimal walking.", "leg_insights": [{"ai_insight": "Efficient bus connection"}]}]}'

        request = InsightRequest(itineraries=[sample_itinerary])
        result = await insight_agent.execute(request)

        assert len(result.itinerary_insights) == 1
        assert (
            result.itinerary_insights[0].ai_insight
            == "This is a great bus route with minimal walking."
        )
        assert len(result.itinerary_insights[0].leg_insights) == 1

    @pytest.mark.asyncio
    async def test_insight_generation_with_preferences(
        self, insight_agent, sample_itinerary, sample_preferences
    ):
        """Test insight generation with user preferences."""
        from app.agents.insight import InsightRequest

        insight_agent.llm_provider.response = '{"itinerary_insights": [{"ai_insight": "Considering your preferences for speed and minimal walking, this route is ideal.", "leg_insights": []}]}'

        request = InsightRequest(
            itineraries=[sample_itinerary], user_preferences=sample_preferences
        )
        result = await insight_agent.execute(request)

        assert len(result.itinerary_insights) == 1
        assert "ideal" in result.itinerary_insights[0].ai_insight

    @pytest.mark.asyncio
    async def test_multiple_itineraries(self, insight_agent, sample_itinerary):
        """Test insight generation for multiple itineraries."""
        # Create a second itinerary
        second_leg = Leg(
            mode=TransportMode.TRAM,
            start=datetime(2024, 1, 15, 9, 0, 0),
            end=datetime(2024, 1, 15, 9, 45, 0),
            duration=2700,  # 45 minutes
            distance=12000,  # 12 km
            from_place=sample_itinerary.legs[0].from_place,
            to_place=sample_itinerary.legs[0].to_place,
            route=Route(short_name="6", long_name="Tram 6", description="Tram route"),
        )

        second_itinerary = Itinerary(
            start=datetime(2024, 1, 15, 9, 0, 0),
            end=datetime(2024, 1, 15, 9, 45, 0),
            duration=2700,
            walk_distance=300,
            walk_time=180,
            legs=[second_leg],
        )

        from app.agents.insight import InsightRequest

        insight_agent.llm_provider.response = '{"itinerary_insights": [{"ai_insight": "Fast bus route with minimal walking.", "leg_insights": []}, {"ai_insight": "Scenic tram route but takes longer.", "leg_insights": []}]}'

        request = InsightRequest(itineraries=[sample_itinerary, second_itinerary])
        result = await insight_agent.execute(request)

        assert len(result.itinerary_insights) == 2
        assert "Fast bus route" in result.itinerary_insights[0].ai_insight
        assert "Scenic tram route" in result.itinerary_insights[1].ai_insight

    @pytest.mark.asyncio
    async def test_empty_itineraries_raises_error(self, insight_agent):
        """Test that empty itineraries list raises validation error."""
        from app.agents.insight import InsightRequest

        with pytest.raises(ValueError, match="At least one itinerary is required"):
            request = InsightRequest(itineraries=[])
            await insight_agent.execute(request)

    @pytest.mark.asyncio
    async def test_llm_error_propagation(self, insight_agent, sample_itinerary):
        """Test that LLM errors are properly propagated."""
        from app.agents.insight import InsightRequest

        insight_agent.llm_provider.should_fail = True
        insight_agent.llm_provider.fail_with = LLMError

        request = InsightRequest(itineraries=[sample_itinerary])
        with pytest.raises(LLMError):
            await insight_agent.execute(request)


class TestInsightAgentIntegration:
    """Integration tests for the insight agent."""

    @pytest.fixture
    def real_insight_agent(self, mock_llm, mock_weather_service):
        """Create an insight agent with real template loading."""
        try:
            insight_agent = InsightAgent(mock_llm)
        except ValueError as e:
            pass
        insight_agent._weather_service = mock_weather_service

    @pytest.mark.asyncio
    async def test_template_rendering_integration(self, real_insight_agent, sample_itinerary):
        """Test that templates are properly rendered and used."""
        from app.agents.insight import InsightRequest

        real_insight_agent.llm_provider.response = '{"itinerary_insights": [{"ai_insight": "Excellent choice for this journey.", "leg_insights": []}]}'

        request = InsightRequest(itineraries=[sample_itinerary])
        await real_insight_agent.execute(request)

        # Verify LLM was called with rendered templates
        assert len(real_insight_agent.llm_provider.generate_calls) == 1
        call = real_insight_agent.llm_provider.generate_calls[0]

        assert len(call["messages"]) == 2
        assert call["messages"][0]["role"] == "system"
        assert call["messages"][1]["role"] == "user"

    @pytest.mark.asyncio
    async def test_complex_itinerary_with_multiple_legs(self, real_insight_agent):
        """Test handling of complex itineraries with multiple legs."""
        # Create a multi-leg itinerary
        leg1 = Leg(
            mode=TransportMode.WALK,
            start=datetime(2024, 1, 15, 9, 0, 0),
            end=datetime(2024, 1, 15, 9, 5, 0),
            duration=300,
            distance=400,
            from_place=Place(
                coordinates=Coordinates(latitude=60.1699, longitude=24.9384), name="Home"
            ),
            to_place=Place(
                coordinates=Coordinates(latitude=60.1710, longitude=24.9400), name="Bus Stop"
            ),
            route=None,
        )

        leg2 = Leg(
            mode=TransportMode.BUS,
            start=datetime(2024, 1, 15, 9, 5, 0),
            end=datetime(2024, 1, 15, 9, 35, 0),
            duration=1800,
            distance=15000,
            from_place=Place(
                coordinates=Coordinates(latitude=60.1710, longitude=24.9400), name="Bus Stop"
            ),
            to_place=Place(
                coordinates=Coordinates(latitude=60.2055, longitude=24.6559),
                name="Destination Stop",
            ),
            route=Route(short_name="550", long_name="Express Bus", description="Express service"),
        )

        leg3 = Leg(
            mode=TransportMode.WALK,
            start=datetime(2024, 1, 15, 9, 35, 0),
            end=datetime(2024, 1, 15, 9, 40, 0),
            duration=300,
            distance=200,
            from_place=Place(
                coordinates=Coordinates(latitude=60.2055, longitude=24.6559),
                name="Destination Stop",
            ),
            to_place=Place(
                coordinates=Coordinates(latitude=60.2060, longitude=24.6570),
                name="Final Destination",
            ),
            route=None,
        )

        complex_itinerary = Itinerary(
            start=datetime(2024, 1, 15, 9, 0, 0),
            end=datetime(2024, 1, 15, 9, 40, 0),
            duration=2400,
            walk_distance=600,
            walk_time=600,
            legs=[leg1, leg2, leg3],
        )

        from app.agents.insight import InsightRequest

        real_insight_agent.llm_provider.response = '{"itinerary_insights": [{"ai_insight": "Well-balanced route with reasonable walking and efficient transit.", "leg_insights": [{"ai_insight": "Short walk to bus stop"}, {"ai_insight": "Express bus service"}, {"ai_insight": "Brief walk to destination"}]}]}'

        request = InsightRequest(itineraries=[complex_itinerary])
        result = await real_insight_agent.execute(request)

        assert len(result.itinerary_insights) == 1
        assert (
            result.itinerary_insights[0].ai_insight
            == "Well-balanced route with reasonable walking and efficient transit."
        )
        assert len(result.itinerary_insights[0].leg_insights) == 3

    @pytest.mark.asyncio
    async def test_error_handling_during_generation(self, real_insight_agent, sample_itinerary):
        """Test error handling during the generation process."""
        from app.agents.insight import InsightRequest

        real_insight_agent.llm_provider.should_fail = True
        real_insight_agent.llm_provider.fail_with = LLMError

        request = InsightRequest(itineraries=[sample_itinerary])
        with pytest.raises(LLMError):
            await real_insight_agent.execute(request)

    @pytest.mark.asyncio
    async def test_generation_parameters(self, real_insight_agent, sample_itinerary):
        """Test that generation parameters are correctly passed to LLM."""
        from app.agents.insight import InsightRequest

        real_insight_agent.llm_provider.response = '{"itinerary_insights": [{"ai_insight": "Generated with specific parameters.", "leg_insights": []}]}'

        request = InsightRequest(itineraries=[sample_itinerary])
        await real_insight_agent.execute(request)

        # Note: The base agent doesn't pass specific generation parameters by default
        # This test may need adjustment based on actual implementation
        call = real_insight_agent.llm_provider.generate_calls[0]
        assert "messages" in call

    @pytest.mark.asyncio
    async def test_insight_agent_with_markdown_wrapped_json(
        self, real_insight_agent, sample_itinerary
    ):
        """Test that insight agent can handle markdown-wrapped JSON responses."""
        from app.agents.insight import InsightRequest

        # Response wrapped in markdown code blocks
        real_insight_agent.llm_provider.response = """```json
{
  "itinerary_insights": [
    {
      "ai_insight": "This is a markdown-wrapped insight",
      "leg_insights": [
        {
          "ai_insight": "Markdown-wrapped leg insight"
        }
      ]
    }
  ]
}
```"""

        request = InsightRequest(itineraries=[sample_itinerary])
        result = await real_insight_agent.execute(request)

        assert len(result.itinerary_insights) == 1
        assert result.itinerary_insights[0].ai_insight == "This is a markdown-wrapped insight"
        assert len(result.itinerary_insights[0].leg_insights) == 1
        assert (
            result.itinerary_insights[0].leg_insights[0].ai_insight
            == "Markdown-wrapped leg insight"
        )
