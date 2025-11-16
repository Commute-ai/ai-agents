"""
Insight agent for generating AI-powered travel itinerary analysis.
"""

import logging

from pydantic import BaseModel, field_validator

from app.agents.base import BaseAgent
from app.llm.base import LLMProvider
from app.schemas.itinerary import Itinerary, ItineraryInsight
from app.schemas.preference import Preference
from app.schemas.weather import WeatherCondition

logger = logging.getLogger(__name__)


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
        super().__init__(llm_provider)
