from typing import cast

from app.agents.insight.agent import InsightAgent, InsightRequest, InsightResponse
from app.llm.factory import LLMProviderFactory, LLMProviderType
from app.schemas.itinerary import Itinerary, ItineraryInsight
from app.schemas.preference import Preference


class InsightService:
    """Business layer service for generating travel itinerary insights."""

    def __init__(self):
        """Initialize the service with an LLM provider."""
        llm_provider = LLMProviderFactory.create_provider(provider=LLMProviderType.GROQ)
        self.insight_agent = InsightAgent(llm_provider)

    async def generate_insights(
        self, itineraries: list[Itinerary], user_preferences: list[Preference] | None = None
    ) -> list[ItineraryInsight]:
        """Generate AI insights for a list of travel itineraries."""

        if len(itineraries) == 0:
            raise ValueError("At least one itinerary is required")

        # Create request for the insight agent
        request = InsightRequest(itineraries=itineraries, user_preferences=user_preferences)

        # Execute the agent
        response = cast(InsightResponse, await self.insight_agent.execute(request))

        return response.itinerary_insights
