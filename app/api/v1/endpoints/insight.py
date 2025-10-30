from fastapi import APIRouter
from pydantic import BaseModel

from app.schemas.itinerary import Itinerary, ItineraryWithInsight
from app.schemas.preference import Preference

router = APIRouter()


class ItinerariesRequest(BaseModel):
    itineraries: list[Itinerary]
    user_preferences: list[Preference] | None = None


class ItinerariesResponse(BaseModel):
    itineraries: list[ItineraryWithInsight]


@router.post("/itineraries", response_model=ItinerariesResponse)
async def generate_itineraries_with_insights(request: ItinerariesRequest):
    itineraries_with_insight: list[ItineraryWithInsight] = []
    for itinerary in request.itineraries:
        itinerary_with_insight = ItineraryWithInsight(
            **itinerary.model_dump(), ai_insight="This is a placeholder insight"
        )
        itineraries_with_insight.append(itinerary_with_insight)

    return ItinerariesResponse(itineraries=itineraries_with_insight)
