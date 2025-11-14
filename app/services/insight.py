from app.agents.insight.agent import InsightAgent, InsightRequest
from app.llm.factory import LLMProviderFactory, LLMProviderType
from app.schemas.itinerary import Itinerary, ItineraryInsight
from app.schemas.preference import Preference
from app.services.weather import WeatherService


class InsightService:
    """Business layer service for generating travel itinerary insights."""

    def __init__(self):
        """Initialize the service with an LLM provider and optional weather service."""
        llm_provider = LLMProviderFactory.create_provider(provider=LLMProviderType.GROQ)

        # Try to create weather service, but don't fail if it can't be initialized
        try:
            weather_service = WeatherService()
        except ValueError:
            # Weather service can't be initialized (likely missing API key)
            # This is fine - insights will work without weather data
            weather_service = None

        self.insight_agent = InsightAgent(llm_provider, weather_service)

    async def generate_insights(
        self, itineraries: list[Itinerary], user_preferences: list[Preference] | None = None
    ) -> list[ItineraryInsight]:
        """Generate AI insights for a list of travel itineraries."""

        if len(itineraries) == 0:
            raise ValueError("At least one itinerary is required")

        # Create request for the insight agent
        request = InsightRequest(itineraries=itineraries, user_preferences=user_preferences)

        # Execute the agent
        response = await self.insight_agent.execute(request)

        return response.itinerary_insights
