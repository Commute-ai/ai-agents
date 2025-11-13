"""
Insight agent for generating AI-powered travel itinerary analysis.
"""

from pydantic import BaseModel, field_validator

from app.agents.base import BaseAgent
from app.llm.base import LLMProvider
from app.schemas.itinerary import Itinerary, ItineraryInsight
from app.schemas.preference import Preference
from app.schemas.weather import WeatherCondition
from app.services.weather import WeatherService


class InsightRequest(BaseModel):
    """Request schema for insight generation."""

    itineraries: list[Itinerary]
    user_preferences: list[Preference] | None = None
    weather_conditions: WeatherCondition | None = None

    @field_validator("itineraries")
    @classmethod
    def validate_itineraries(cls, v):
        if not v:
            raise ValueError("At least one itinerary is required")
        return v


class InsightResponse(BaseModel):
    """Response schema for insight generation."""

    itinerary_insights: list[ItineraryInsight]


class InsightAgent(BaseAgent):
    """AI agent for generating insights about travel itineraries."""

    input_model = InsightRequest
    output_model = InsightResponse

    def __init__(self, llm_provider: LLMProvider):
        """Initialize the insight agent with an LLM provider."""
        super().__init__(llm_provider)
        self._weather_service = WeatherService()

    async def _get_weather_for_itinerary(self, itinerary: Itinerary) -> WeatherCondition | None:
        """Get weather conditions for an itinerary's start location and time."""
        try:
            # Extract coordinates from the first leg's from_place if available
            if itinerary.legs and itinerary.legs[0].from_place:
                coordinates = itinerary.legs[0].from_place.coordinates
                lat = coordinates.latitude
                lon = coordinates.longitude
            else:
                # Default to Helsinki coordinates
                lat, lon = 60.1695, 24.9354

            return await self._weather_service.get_current_weather(lat=lat, lon=lon)
        except Exception:
            # Return None if weather fetch fails - agent should still work without weather
            return None

    async def execute(self, input_data: InsightRequest) -> InsightResponse:
        """Execute insight generation with weather context."""
        # Enhance request with weather data if not provided
        if not input_data.weather_conditions and input_data.itineraries:
            # Use the start time of the first itinerary to determine weather context
            first_itinerary = input_data.itineraries[0]
            weather_conditions = await self._get_weather_for_itinerary(first_itinerary)

            # Create enhanced request with weather data
            enhanced_request = InsightRequest(
                itineraries=input_data.itineraries,
                user_preferences=input_data.user_preferences,
                weather_conditions=weather_conditions,
            )
        else:
            enhanced_request = input_data

        return await super().execute(enhanced_request)
