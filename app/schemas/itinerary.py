"""
Itinerary Schema

Pydantic models for representing transit routes and itineraries.
"""

from collections.abc import Sequence
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from app.schemas.location import Place


class TransportMode(str, Enum):
    """Transport modes."""

    WALK = "WALK"
    BICYCLE = "BICYCLE"
    CAR = "CAR"
    TRAM = "TRAM"
    SUBWAY = "SUBWAY"
    RAIL = "RAIL"
    BUS = "BUS"
    FERRY = "FERRY"


class Route(BaseModel):
    """Route information for a leg of the journey."""

    short_name: str = Field(..., description="Short name of the route, e.g., bus number")
    long_name: str = Field(..., description="Long name of the route, e.g., full route name")
    description: str | None = Field(None, description="Description of the route")


class Leg(BaseModel):
    """A single segment of a journey."""

    mode: TransportMode
    start: datetime
    end: datetime
    duration: int = Field(..., description="Duration in seconds")
    distance: float = Field(..., description="Distance in meters")
    from_place: Place
    to_place: Place
    route: Route | None = None


class Itinerary(BaseModel):
    """A complete journey from origin to destination."""

    start: datetime
    end: datetime
    duration: int = Field(..., description="Total duration in seconds")
    walk_distance: float = Field(..., description="Total walking distance in meters")
    walk_time: int = Field(..., description="Total walking time in seconds")
    legs: Sequence[Leg]


class LegInsight(BaseModel):
    """Insight information for a single leg of the itinerary."""

    ai_insight: str = Field(..., description="AI-generated insight about the leg")


class ItineraryInsight(BaseModel):
    """Insight information for a given itinerary."""

    ai_insight: str = Field(..., description="AI-generated insight about the itinerary")
    leg_insights: list[LegInsight] = Field(..., description="List of insights for each leg")
