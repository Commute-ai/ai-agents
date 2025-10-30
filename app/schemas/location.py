"""
Location Schema

Pydantic models for representing places and locations.
"""

from pydantic import BaseModel

from app.schemas.geo import Coordinates


class Place(BaseModel):
    """A place with metadata"""

    coordinates: Coordinates
    name: str | None = None
