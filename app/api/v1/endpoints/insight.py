from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.agents.insight import InsightAgent
from app.schemas.itinerary import Itinerary, ItineraryWithInsight
from app.schemas.preference import Preference
from app.services.llm import LLMError, create_llm_from_config

router = APIRouter()


class ItinerariesRequest(BaseModel):
    itineraries: list[Itinerary]
    user_preferences: list[Preference] | None = None


class ItinerariesResponse(BaseModel):
    itineraries: list[ItineraryWithInsight]


@router.post("/itineraries", response_model=ItinerariesResponse)
async def generate_itineraries_with_insights(request: ItinerariesRequest):
    """
    Generate AI insights for travel itineraries.

    Uses the configured LLM provider (Groq by default) to analyze routes
    and provide helpful recommendations based on duration, walking distance,
    transfers, and user preferences.
    """
    try:
        # Create LLM provider from configuration
        llm_provider = create_llm_from_config()

        # Initialize insight agent
        insight_agent = InsightAgent(llm_provider)

        # Generate insights for all itineraries
        itineraries_with_insight = await insight_agent.run(
            request.itineraries, request.user_preferences
        )

        return ItinerariesResponse(itineraries=itineraries_with_insight)

    except LLMError as e:
        raise HTTPException(
            status_code=503, detail=f"AI service temporarily unavailable: {str(e)}"
        ) from e
    except ValueError as e:
        raise HTTPException(status_code=500, detail=f"Configuration error: {str(e)}") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") from e
