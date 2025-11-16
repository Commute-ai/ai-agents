import logging

from app.agents.insight.agent import InsightAgent, InsightRequest
from app.llm.factory import LLMProviderFactory, LLMProviderType
from app.schemas.geo import Coordinates
from app.schemas.itinerary import Itinerary, ItineraryInsight
from app.schemas.preference import Preference
from app.schemas.weather import WeatherCondition
from app.services.weather import WeatherService, WeatherServiceError

logger = logging.getLogger(__name__)


class InsightService:
    """Business layer service for generating travel itinerary insights."""

    def __init__(self):
        """Initialize the service with an LLM provider and optional weather service."""
        llm_provider = LLMProviderFactory.create_provider(provider=LLMProviderType.GROQ)

        # Try to create weather service, but don't fail if it can't be initialized
        try:
            self._weather_service: WeatherService | None = WeatherService()
        except ValueError as error:
            # Weather service can't be initialized (likely missing API key)
            # This is fine - insights will work without weather data
            logging.warning("Weather service is not configured, proceeding without it: ", str(error))
            self._weather_service = None

        self.insight_agent = InsightAgent(llm_provider)

    async def _get_weather_for_itinerary(self, itinerary: Itinerary) -> WeatherCondition | None:
        """Get weather conditions for an itinerary's start location and time."""
        if not self._weather_service:
            return None

        try:
            # Extract coordinates from the first leg's from_place if available
            if itinerary.legs and itinerary.legs[0].from_place:
                coordinates = itinerary.legs[0].from_place.coordinates
            else:
                # Default to Helsinki coordinates
                coordinates = Coordinates(latitude=60.1695, longitude=24.9354)

            return await self._weather_service.get_current_weather(coordinates)
        except (ValueError, WeatherServiceError) as error:
            logger.warning(f"Failed to get weather conditions for itinerary: {error}")
            return None

    async def generate_insights(
        self, itineraries: list[Itinerary], user_preferences: list[Preference] | None = None
    ) -> list[ItineraryInsight]:
        """Generate AI insights for a list of travel itineraries."""

        if len(itineraries) == 0:
            raise ValueError("At least one itinerary is required")

        # Get weather conditions for the first itinerary
        weather_conditions = None
        if itineraries:
            weather_conditions = await self._get_weather_for_itinerary(itineraries[0])

        logging.info(weather_conditions)

        if not weather_conditions:
            logger.warning("Weather data is not available for insight generation")

        # Create request for the insight agent with weather data
        request = InsightRequest(
            itineraries=itineraries,
            user_preferences=user_preferences,
            weather_conditions=weather_conditions,
        )

        # Execute the agent
        response = await self.insight_agent.execute(request)

        return response.itinerary_insights
