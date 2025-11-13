from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.dependencies import get_insight_service
from app.llm.base import LLMError
from app.schemas.itinerary import Itinerary, ItineraryInsight
from app.schemas.preference import Preference
from app.services.insight import InsightService

router = APIRouter()


class ItinerariesRequest(BaseModel):
    itineraries: list[Itinerary]
    user_preferences: list[Preference] | None = None


class ItinerariesResponse(BaseModel):
    itinerary_insights: list[ItineraryInsight]


@router.post("/itineraries", response_model=ItinerariesResponse)
async def generate_itineraries_with_insights(
    request: ItinerariesRequest, insight_service: InsightService = Depends(get_insight_service)
):
    """
    Generate AI insights for travel itineraries.
    """
    try:
        # Generate insights using the service
        insights = await insight_service.generate_insights(
            itineraries=request.itineraries, user_preferences=request.user_preferences
        )

        return ItinerariesResponse(itinerary_insights=insights)

    except LLMError as e:
        raise HTTPException(
            status_code=503, detail=f"AI service temporarily unavailable: {str(e)}"
        ) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") from e
