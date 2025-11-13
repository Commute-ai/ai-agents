"""Weather related type definitions."""

from datetime import datetime

from pydantic import BaseModel


class WeatherCondition(BaseModel):
    """Weather condition data."""

    temperature: float  # in Celsius
    description: str  # e.g., "light rain", "clear sky"
    humidity: int  # percentage
    wind_speed: float  # in m/s
    precipitation: float  # in mm/h
    timestamp: datetime
