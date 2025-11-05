from typing import cast

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.agents.insight import InsightRequest, InsightResponse
from app.dependencies import InsightAgentDep
from app.schemas.itinerary import Itinerary, ItineraryInsight
from app.schemas.preference import Preference
from app.services.llm import LLMError

router = APIRouter()


class ItinerariesRequest(BaseModel):
    itineraries: list[Itinerary]
    user_preferences: list[Preference] | None = None


class ItinerariesResponse(BaseModel):
    itinerary_insights: list[ItineraryInsight]


@router.post("/itineraries", response_model=ItinerariesResponse)
async def generate_itineraries_with_insights(
    request: ItinerariesRequest, insight_agent: InsightAgentDep
):
    """
    Generate AI insights for travel itineraries.

    Uses the configured LLM provider (Groq by default) to analyze routes
    and provide helpful recommendations based on duration, walking distance,
    transfers, and user preferences.
    """
    try:
        # Create insight request
        insight_request = InsightRequest(
            itineraries=request.itineraries, user_preferences=request.user_preferences
        )

        # Generate insights using the agent
        insight_response = cast(InsightResponse, await insight_agent.execute(insight_request))

        return ItinerariesResponse(itinerary_insights=insight_response.itinerary_insights)

    except LLMError as e:
        raise HTTPException(
            status_code=503, detail=f"AI service temporarily unavailable: {str(e)}"
        ) from e
    except ValueError as e:
        raise HTTPException(status_code=500, detail=f"Configuration error: {str(e)}") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") from e
