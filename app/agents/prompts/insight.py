"""
Prompt templates for the insight agent.
"""


class InsightPrompts:
    """
    Collection of prompt templates for generating travel itinerary insights.
    """

    def get_system_prompt(self) -> str:
        """
        Get the system prompt that defines the agent's role and behavior.

        Returns:
            System prompt for the insight agent
        """
        return """You are a travel route analyst AI assistant. Your job is to analyze transit itineraries and provide helpful, concise insights to travelers.

When analyzing routes, consider:
- Total journey time and walking distance
- Number of transfers and connections
- Transport modes used (walking, bus, rail, etc.)
- Potential advantages and disadvantages
- User preferences when provided

Provide insights that are:
- Practical and actionable
- Focused on pros and cons
- Concise (2-3 sentences maximum)
- Helpful for decision-making
- Considerate of accessibility and comfort factors

Focus on what makes this route unique, efficient, or challenging compared to typical alternatives."""

    def build_insight_prompt(
        self, formatted_itinerary: str, formatted_preferences: str | None = None
    ) -> str:
        """
        Build the user prompt for generating insights about an itinerary.

        Args:
            formatted_itinerary: Human-readable itinerary description
            formatted_preferences: Optional formatted user preferences

        Returns:
            Complete user prompt for insight generation
        """
        prompt_parts = [
            "Please analyze the following travel itinerary and provide a helpful insight:",
            "",
            formatted_itinerary,
        ]

        if formatted_preferences:
            prompt_parts.extend(["", formatted_preferences])

        prompt_parts.extend(
            [
                "",
                "Generate a concise insight that highlights the key advantages or considerations for this route. Focus on practical travel advice.",
            ]
        )

        return "\n".join(prompt_parts)

    def build_comparison_prompt(
        self, itineraries_data: list[str], formatted_preferences: str | None = None
    ) -> str:
        """
        Build a prompt for comparing multiple itineraries.

        Args:
            itineraries_data: List of formatted itinerary descriptions
            formatted_preferences: Optional formatted user preferences

        Returns:
            Prompt for comparing multiple routes
        """
        prompt_parts = [
            "Please compare the following travel route options and provide insights for each:",
            "",
        ]

        for i, itinerary in enumerate(itineraries_data, 1):
            prompt_parts.extend([f"Route Option {i}:", itinerary, ""])

        if formatted_preferences:
            prompt_parts.extend([formatted_preferences, ""])

        prompt_parts.extend(
            [
                "For each route, provide a brief insight that highlights its key characteristics,",
                "advantages, or considerations. Keep insights concise and practical.",
            ]
        )

        return "\n".join(prompt_parts)
