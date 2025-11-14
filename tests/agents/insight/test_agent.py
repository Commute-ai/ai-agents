"""Tests for the insight agent."""

from datetime import datetime
from unittest.mock import patch

import pytest

from app.agents.insight import InsightAgent, InsightRequest
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
    """Create a mock LLM provider for testing."""
    return MockLLMProvider()


@pytest.fixture
def mock_weather_service():
    """Create a mock weather service for testing."""
    return MockWeatherService()


@pytest.fixture
def sample_itinerary():
    """Create a sample itinerary for testing."""
    start_place = Place(
        coordinates=Coordinates(latitude=60.1699, longitude=24.9384), name="Helsinki Central"
    )
    end_place = Place(
        coordinates=Coordinates(latitude=60.2055, longitude=24.6559), name="Espoo Central"
    )

    route = Route(
        short_name="550",
        long_name="Helsinki - Espoo",
        description="Bus route from Helsinki to Espoo",
    )

    leg = Leg(
        mode=TransportMode.BUS,
        start=datetime(2024, 1, 15, 9, 0, 0),
        end=datetime(2024, 1, 15, 9, 30, 0),
        duration=1800,  # 30 minutes
        distance=15000,  # 15 km
        from_place=start_place,
        to_place=end_place,
        route=route,
    )

    return Itinerary(
        start=datetime(2024, 1, 15, 9, 0, 0),
        end=datetime(2024, 1, 15, 9, 30, 0),
        duration=1800,
        walk_distance=200,
        walk_time=120,
        legs=[leg],
    )


@pytest.fixture
def sample_preferences():
    """Create sample user preferences for testing."""
    return [
        Preference(prompt="I prefer faster routes"),
        Preference(prompt="I want to minimize walking"),
    ]


class TestInsightAgent:
    """Test the InsightAgent class with mocked dependencies."""

    @pytest.fixture
    def insight_agent(self, mock_llm, mock_weather_service):
        """Create an insight agent with mocked dependencies."""
        with patch("app.agents.insight.agent.WeatherService") as mock_weather_class:
            mock_weather_class.return_value = mock_weather_service
            agent = InsightAgent(mock_llm)
            return agent

    @pytest.mark.asyncio
    async def test_successful_insight_generation(self, insight_agent, sample_itinerary):
        """Test successful insight generation for a single itinerary."""
        insight_agent.llm_provider.response = (
            '{"itinerary_insights": [{"ai_insight": "This is a great bus route with minimal walking.", '
            '"leg_insights": [{"ai_insight": "Efficient bus connection"}]}]}'
        )

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
        insight_agent.llm_provider.response = (
            '{"itinerary_insights": [{"ai_insight": "Considering your preferences for speed and '
            'minimal walking, this route is ideal.", "leg_insights": []}]}'
        )

        request = InsightRequest(
            itineraries=[sample_itinerary], user_preferences=sample_preferences
        )
        result = await insight_agent.execute(request)

        assert len(result.itinerary_insights) == 1
        assert "ideal" in result.itinerary_insights[0].ai_insight

    @pytest.mark.asyncio
    async def test_multiple_itineraries(self, insight_agent, sample_itinerary):
        """Test insight generation for multiple itineraries."""
        # Create a second itinerary with tram
        tram_leg = Leg(
            mode=TransportMode.TRAM,
            start=datetime(2024, 1, 15, 9, 0, 0),
            end=datetime(2024, 1, 15, 9, 45, 0),
            duration=2700,  # 45 minutes
            distance=12000,  # 12 km
            from_place=sample_itinerary.legs[0].from_place,
            to_place=sample_itinerary.legs[0].to_place,
            route=Route(short_name="6", long_name="Tram 6", description="Tram route"),
        )

        tram_itinerary = Itinerary(
            start=datetime(2024, 1, 15, 9, 0, 0),
            end=datetime(2024, 1, 15, 9, 45, 0),
            duration=2700,
            walk_distance=300,
            walk_time=180,
            legs=[tram_leg],
        )

        insight_agent.llm_provider.response = (
            '{"itinerary_insights": ['
            '{"ai_insight": "Fast bus route with minimal walking.", "leg_insights": []}, '
            '{"ai_insight": "Scenic tram route but takes longer.", "leg_insights": []}]}'
        )

        request = InsightRequest(itineraries=[sample_itinerary, tram_itinerary])
        result = await insight_agent.execute(request)

        assert len(result.itinerary_insights) == 2
        assert "Fast bus route" in result.itinerary_insights[0].ai_insight
        assert "Scenic tram route" in result.itinerary_insights[1].ai_insight

    @pytest.mark.asyncio
    async def test_empty_itineraries_raises_error(self, insight_agent):
        """Test that empty itineraries list raises validation error."""
        with pytest.raises(ValueError, match="At least one itinerary is required"):
            InsightRequest(itineraries=[])

    @pytest.mark.asyncio
    async def test_llm_error_propagation(self, insight_agent, sample_itinerary):
        """Test that LLM errors are properly propagated."""
        insight_agent.llm_provider.should_fail = True
        insight_agent.llm_provider.fail_with = LLMError

        request = InsightRequest(itineraries=[sample_itinerary])
        with pytest.raises(LLMError):
            await insight_agent.execute(request)

    @pytest.mark.asyncio
    async def test_weather_service_integration(self, insight_agent, sample_itinerary):
        """Test that weather service is called and integrates properly."""
        insight_agent.llm_provider.response = '{"itinerary_insights": [{"ai_insight": "Great weather for traveling!", "leg_insights": []}]}'

        request = InsightRequest(itineraries=[sample_itinerary])
        result = await insight_agent.execute(request)

        # Verify weather service was called
        assert not insight_agent._weather_service.should_fail
        assert len(result.itinerary_insights) == 1

    @pytest.mark.asyncio
    async def test_weather_service_failure_handling(self, insight_agent, sample_itinerary):
        """Test that agent works even when weather service fails."""
        # Make weather service fail
        insight_agent._weather_service.should_fail = True

        insight_agent.llm_provider.response = '{"itinerary_insights": [{"ai_insight": "Route works regardless of weather.", "leg_insights": []}]}'

        request = InsightRequest(itineraries=[sample_itinerary])
        result = await insight_agent.execute(request)

        # Agent should still work despite weather service failure
        assert len(result.itinerary_insights) == 1
        assert "Route works regardless" in result.itinerary_insights[0].ai_insight


class TestInsightAgentTemplates:
    """Test template rendering and LLM integration."""

    @pytest.fixture
    def template_agent(self, mock_llm, mock_weather_service):
        """Create an insight agent with mocked weather service for template testing."""
        with patch("app.agents.insight.agent.WeatherService") as mock_weather_class:
            mock_weather_class.return_value = mock_weather_service
            agent = InsightAgent(mock_llm)
            return agent

    @pytest.mark.asyncio
    async def test_template_rendering_integration(self, template_agent, sample_itinerary):
        """Test that templates are properly rendered and used."""
        template_agent.llm_provider.response = '{"itinerary_insights": [{"ai_insight": "Excellent choice for this journey.", "leg_insights": []}]}'

        request = InsightRequest(itineraries=[sample_itinerary])
        await template_agent.execute(request)

        # Verify LLM was called with rendered templates
        assert len(template_agent.llm_provider.generate_calls) == 1
        call = template_agent.llm_provider.generate_calls[0]

        assert len(call["messages"]) == 2
        assert call["messages"][0]["role"] == "system"
        assert call["messages"][1]["role"] == "user"

    @pytest.mark.asyncio
    async def test_complex_multi_leg_itinerary(self, template_agent):
        """Test handling of complex itineraries with multiple legs."""
        # Create a multi-leg itinerary: walk -> bus -> walk
        home = Place(coordinates=Coordinates(latitude=60.1699, longitude=24.9384), name="Home")
        bus_stop = Place(
            coordinates=Coordinates(latitude=60.1710, longitude=24.9400), name="Bus Stop"
        )
        dest_stop = Place(
            coordinates=Coordinates(latitude=60.2055, longitude=24.6559), name="Destination Stop"
        )
        destination = Place(
            coordinates=Coordinates(latitude=60.2060, longitude=24.6570), name="Final Destination"
        )

        legs = [
            Leg(
                mode=TransportMode.WALK,
                start=datetime(2024, 1, 15, 9, 0, 0),
                end=datetime(2024, 1, 15, 9, 5, 0),
                duration=300,
                distance=400,
                from_place=home,
                to_place=bus_stop,
                route=None,
            ),
            Leg(
                mode=TransportMode.BUS,
                start=datetime(2024, 1, 15, 9, 5, 0),
                end=datetime(2024, 1, 15, 9, 35, 0),
                duration=1800,
                distance=15000,
                from_place=bus_stop,
                to_place=dest_stop,
                route=Route(
                    short_name="550", long_name="Express Bus", description="Express service"
                ),
            ),
            Leg(
                mode=TransportMode.WALK,
                start=datetime(2024, 1, 15, 9, 35, 0),
                end=datetime(2024, 1, 15, 9, 40, 0),
                duration=300,
                distance=200,
                from_place=dest_stop,
                to_place=destination,
                route=None,
            ),
        ]

        complex_itinerary = Itinerary(
            start=datetime(2024, 1, 15, 9, 0, 0),
            end=datetime(2024, 1, 15, 9, 40, 0),
            duration=2400,
            walk_distance=600,
            walk_time=600,
            legs=legs,
        )

        template_agent.llm_provider.response = (
            '{"itinerary_insights": [{"ai_insight": "Well-balanced route with reasonable walking and efficient transit.", '
            '"leg_insights": [{"ai_insight": "Short walk to bus stop"}, {"ai_insight": "Express bus service"}, '
            '{"ai_insight": "Brief walk to destination"}]}]}'
        )

        request = InsightRequest(itineraries=[complex_itinerary])
        result = await template_agent.execute(request)

        assert len(result.itinerary_insights) == 1
        assert (
            result.itinerary_insights[0].ai_insight
            == "Well-balanced route with reasonable walking and efficient transit."
        )
        assert len(result.itinerary_insights[0].leg_insights) == 3

    @pytest.mark.asyncio
    async def test_llm_call_parameters(self, template_agent, sample_itinerary):
        """Test that LLM is called with correct parameters."""
        template_agent.llm_provider.response = '{"itinerary_insights": [{"ai_insight": "Generated with correct params.", "leg_insights": []}]}'

        request = InsightRequest(itineraries=[sample_itinerary])
        await template_agent.execute(request)

        # Verify LLM was called with proper message structure
        assert len(template_agent.llm_provider.generate_calls) == 1
        call = template_agent.llm_provider.generate_calls[0]
        assert "messages" in call
        assert len(call["messages"]) == 2
        assert call["messages"][0]["role"] == "system"
        assert call["messages"][1]["role"] == "user"

    @pytest.mark.asyncio
    async def test_markdown_wrapped_json_response(self, template_agent, sample_itinerary):
        """Test that agent handles markdown-wrapped JSON responses correctly."""
        # Response wrapped in markdown code blocks
        template_agent.llm_provider.response = """```json
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
        result = await template_agent.execute(request)

        assert len(result.itinerary_insights) == 1
        assert result.itinerary_insights[0].ai_insight == "This is a markdown-wrapped insight"
        assert len(result.itinerary_insights[0].leg_insights) == 1
        assert (
            result.itinerary_insights[0].leg_insights[0].ai_insight
            == "Markdown-wrapped leg insight"
        )
