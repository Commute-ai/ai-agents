"""
Insight agent for generating AI-powered travel itinerary analysis.
"""

from app.schemas.itinerary import Itinerary, ItineraryWithInsight, LegWithInsight
from app.schemas.preference import Preference
from app.services.llm.base import LLMProvider

from .base import AgentValidationError, BaseAgent
from .prompts.insight import InsightPrompts


class InsightAgent(BaseAgent):
    """
    AI agent for generating insights about travel itineraries.

    Analyzes transit routes and provides helpful recommendations based on
    duration, walking distance, transfers, and user preferences.
    """

    def __init__(self, llm_provider: LLMProvider) -> None:
        """
        Initialize the insight agent.

        Args:
            llm_provider: LLM provider for generating insights
        """
        super().__init__(llm_provider)
        self.prompts = InsightPrompts()

    async def run(
        self, itineraries: list[Itinerary], user_preferences: list[Preference] | None = None
    ) -> list[ItineraryWithInsight]:
        """
        Execute the insight generation task.
        """

        return await self._generate_insights(itineraries, user_preferences)

    async def _generate_insights(
        self, itineraries: list[Itinerary], user_preferences: list[Preference] | None = None
    ) -> list[ItineraryWithInsight]:
        if not itineraries:
            raise AgentValidationError("At least one itinerary is required")

        # Format all itineraries for the LLM
        formatted_itineraries = [self._format_itinerary(itinerary) for itinerary in itineraries]

        # Format user preferences if provided
        formatted_preferences = None
        if user_preferences:
            formatted_preferences = self._format_preferences(user_preferences)

        # Build the user prompt for multiple itineraries
        user_prompt = self.prompts.build_comparison_prompt(
            formatted_itineraries, formatted_preferences
        )

        # Generate insights using LLM
        response = await self._generate_response(
            user_prompt=user_prompt,
            system_prompt=self.prompts.get_system_prompt(),
            max_tokens=1000,
            temperature=0.7,
        )

        # Parse the response to extract individual insights
        insights = self._parse_insights_response(response, len(itineraries))

        # Create ItineraryWithInsight objects
        result = []
        for itinerary, insight in zip(itineraries, insights, strict=True):
            # Convert legs to LegWithInsight (no individual leg insights for now)
            legs_with_insight = [
                LegWithInsight(**leg.model_dump(), ai_insight=None) for leg in itinerary.legs
            ]

            itinerary_with_insight = ItineraryWithInsight(
                **itinerary.model_dump(exclude={"legs"}), legs=legs_with_insight, ai_insight=insight
            )
            result.append(itinerary_with_insight)

        return result

    def _format_itinerary(self, itinerary: Itinerary) -> str:
        """
        Format itinerary data into human-readable text for the LLM.
        """
        lines = []

        # Overall journey summary
        total_duration = itinerary.duration
        total_walking = itinerary.walk_distance
        lines.append(f"Journey Duration: {total_duration} minutes")
        lines.append(f"Total Walking: {total_walking} meters")
        lines.append(f"Number of Legs: {len(itinerary.legs)}")
        lines.append("")

        # Format each leg
        lines.append("Route Details:")
        for i, leg in enumerate(itinerary.legs, 1):
            leg_info = f"  {i}. {leg.mode.value}"

            if leg.from_place and leg.to_place:
                leg_info += f" from {leg.from_place.name} to {leg.to_place.name}"

            if leg.duration:
                leg_info += f" ({leg.duration} min"
                if leg.distance:
                    leg_info += f", {leg.distance}m"
                leg_info += ")"

            if leg.route and leg.route.short_name:
                leg_info += f" - Route: {leg.route.short_name}"

            lines.append(leg_info)

        return "\n".join(lines)

    def _parse_insights_response(self, response: str, num_itineraries: int) -> list[str]:
        """
        Parse the LLM response to extract individual insights for each itinerary.
        """

        # Simple parsing strategy: split by route markers or use fallback
        insights = []

        # Look for "Route Option N:" patterns
        lines = response.split("\n")
        current_insight: list[str] = []

        for line in lines:
            if line.strip().startswith(("Route Option", "Option")):
                if current_insight:
                    insights.append("\n".join(current_insight).strip())
                    current_insight = []
            elif line.strip():  # Non-empty line
                current_insight.append(line.strip())

        # Add the last insight
        if current_insight:
            insights.append("\n".join(current_insight).strip())

        # Fallback: if parsing didn't work, split response evenly
        if len(insights) != num_itineraries:
            # Simple fallback: use the whole response for each itinerary
            insights = [response.strip()] * num_itineraries

        return insights

    def _format_preferences(self, preferences: list[Preference]) -> str:
        """
        Format user preferences into human-readable text.
        """
        if not preferences:
            return ""

        lines = ["User Preferences:"]
        for pref in preferences:
            pref_line = f"  - {pref.prompt}"
            lines.append(pref_line)

        return "\n".join(lines)
