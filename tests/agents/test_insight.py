"""
Tests for the insight agent.
"""

from datetime import datetime
from unittest.mock import Mock, patch

from jinja2 import DictLoader, Environment
import pytest

from app.agents.base import AgentValidationError
from app.agents.insight import InsightAgent
from app.schemas.geo import Coordinates
from app.schemas.itinerary import (
    Itinerary,
    ItineraryWithInsight,
    Leg,
    LegWithInsight,
    Route,
    TransportMode,
)
from app.schemas.location import Place
from app.schemas.preference import Preference
from app.services.llm.base import LLMError, LLMProvider


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing."""

    def __init__(self, response="Mock insight response", should_fail=False, fail_with=LLMError):
        self.response = response
        self.should_fail = should_fail
        self.fail_with = fail_with
        self.generate_calls = []

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
        if self.should_fail:
            raise self.fail_with("Mock LLM error")

        for chunk in ["Mock ", "streaming ", "response"]:
            yield chunk


@pytest.fixture
def mock_llm():
    return MockLLMProvider()


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
    def insight_agent(self, mock_llm, mock_jinja_env):
        with patch.object(InsightAgent, "__init__", lambda self, llm_provider: None):
            agent = InsightAgent.__new__(InsightAgent)
            agent.llm = mock_llm
            agent.jinja_env = mock_jinja_env
            agent.system_template = mock_jinja_env.get_template("system.j2")
            agent.user_template = mock_jinja_env.get_template("user.j2")
            return agent

    @pytest.mark.asyncio
    async def test_successful_insight_generation(self, insight_agent, sample_itinerary):
        """Test successful insight generation for a single itinerary."""
        insight_agent.llm.response = (
            "Route Option 1:\nThis is a great bus route with minimal walking."
        )

        result = await insight_agent.run([sample_itinerary])

        assert len(result) == 1
        assert isinstance(result[0], ItineraryWithInsight)
        assert result[0].ai_insight == "This is a great bus route with minimal walking."
        assert len(result[0].legs) == 1
        assert isinstance(result[0].legs[0], LegWithInsight)

    @pytest.mark.asyncio
    async def test_insight_generation_with_preferences(
        self, insight_agent, sample_itinerary, sample_preferences
    ):
        """Test insight generation with user preferences."""
        insight_agent.llm.response = "Route Option 1:\nConsidering your preferences for speed and minimal walking, this route is ideal."

        result = await insight_agent.run([sample_itinerary], sample_preferences)

        assert len(result) == 1
        assert "ideal" in result[0].ai_insight

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

        insight_agent.llm.response = """Route Option 1:
Fast bus route with minimal walking.

Route Option 2:
Scenic tram route but takes longer."""

        result = await insight_agent.run([sample_itinerary, second_itinerary])

        assert len(result) == 2
        assert "Fast bus route" in result[0].ai_insight
        assert "Scenic tram route" in result[1].ai_insight

    @pytest.mark.asyncio
    async def test_empty_itineraries_raises_error(self, insight_agent):
        """Test that empty itineraries list raises validation error."""
        with pytest.raises(AgentValidationError, match="At least one itinerary is required"):
            await insight_agent.run([])

    @pytest.mark.asyncio
    async def test_llm_error_propagation(self, insight_agent, sample_itinerary):
        """Test that LLM errors are properly propagated."""
        insight_agent.llm.should_fail = True
        insight_agent.llm.fail_with = LLMError

        with pytest.raises(LLMError):
            await insight_agent.run([sample_itinerary])

    def test_format_itinerary(self, insight_agent, sample_itinerary):
        """Test itinerary formatting for LLM input."""
        formatted = insight_agent._format_itinerary(sample_itinerary)

        assert "Journey Duration: 1800 minutes" in formatted
        assert "Total Walking: 200.0 meters" in formatted
        assert "Number of Legs: 1" in formatted
        assert "BUS" in formatted
        assert "Helsinki Central" in formatted
        assert "Espoo Central" in formatted
        assert "Route: 550" in formatted

    def test_format_preferences(self, insight_agent, sample_preferences):
        """Test preferences formatting."""
        formatted = insight_agent._format_preferences(sample_preferences)

        assert "User Preferences:" in formatted
        assert "I prefer faster routes" in formatted
        assert "I want to minimize walking" in formatted

    def test_format_preferences_empty(self, insight_agent):
        """Test preferences formatting with empty list."""
        formatted = insight_agent._format_preferences([])
        assert formatted == ""

        formatted_none = insight_agent._format_preferences(None)
        assert formatted_none == ""

    def test_parse_insights_response_structured(self, insight_agent):
        """Test parsing of structured LLM response."""
        response = """Route Option 1:
This is the first route insight.
Great for speed.

Route Option 2:
This is the second route insight.
Better for comfort."""

        insights = insight_agent._parse_insights_response(response, 2)

        assert len(insights) == 2
        assert "first route insight" in insights[0]
        assert "second route insight" in insights[1]

    def test_parse_insights_response_fallback(self, insight_agent):
        """Test parsing fallback when structure doesn't match."""
        response = "General insight about all routes without clear structure."

        insights = insight_agent._parse_insights_response(response, 2)

        assert len(insights) == 2
        assert insights[0] == response.strip()
        assert insights[1] == response.strip()

    def test_parse_insights_response_partial_structure(self, insight_agent):
        """Test parsing when only some routes have structured format."""
        response = """Route Option 1:
First route insight.

Some general text without structure.

Route Option 2:
Second route insight."""

        insights = insight_agent._parse_insights_response(response, 2)

        # Should fall back to using same response for all
        assert len(insights) == 2


class TestInsightAgentIntegration:
    """Integration tests for the insight agent."""

    @pytest.fixture
    def real_insight_agent(self, mock_llm):
        """Create an insight agent with real template loading."""
        with patch("pathlib.Path.exists", return_value=True):
            with patch("jinja2.FileSystemLoader"):
                mock_env = Mock()
                mock_system_template = Mock()
                mock_user_template = Mock()

                mock_system_template.render.return_value = "You are a transit expert."
                mock_user_template.render.return_value = "Analyze these routes."

                mock_env.get_template.side_effect = lambda name: (
                    mock_system_template if name == "system.j2" else mock_user_template
                )

                with patch("jinja2.Environment", return_value=mock_env):
                    return InsightAgent(mock_llm)

    @pytest.mark.asyncio
    async def test_template_rendering_integration(self, real_insight_agent, sample_itinerary):
        """Test that templates are properly rendered and used."""
        real_insight_agent.llm.response = "Route Option 1:\nExcellent choice for this journey."

        await real_insight_agent.run([sample_itinerary])

        # Verify LLM was called with rendered templates
        assert len(real_insight_agent.llm.generate_calls) == 1
        call = real_insight_agent.llm.generate_calls[0]

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

        real_insight_agent.llm.response = (
            "Route Option 1:\nWell-balanced route with reasonable walking and efficient transit."
        )

        result = await real_insight_agent.run([complex_itinerary])

        assert len(result) == 1
        itinerary_result = result[0]
        assert len(itinerary_result.legs) == 3
        assert all(isinstance(leg, LegWithInsight) for leg in itinerary_result.legs)
        assert (
            itinerary_result.ai_insight
            == "Well-balanced route with reasonable walking and efficient transit."
        )

    @pytest.mark.asyncio
    async def test_error_handling_during_generation(self, real_insight_agent, sample_itinerary):
        """Test error handling during the generation process."""
        real_insight_agent.llm.should_fail = True
        real_insight_agent.llm.fail_with = LLMError

        with pytest.raises(LLMError):
            await real_insight_agent.run([sample_itinerary])

    @pytest.mark.asyncio
    async def test_generation_parameters(self, real_insight_agent, sample_itinerary):
        """Test that generation parameters are correctly passed to LLM."""
        real_insight_agent.llm.response = "Route Option 1:\nGenerated with specific parameters."

        await real_insight_agent.run([sample_itinerary])

        call = real_insight_agent.llm.generate_calls[0]
        assert call["max_tokens"] == 1000
        assert call["temperature"] == 0.7
