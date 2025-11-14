"""Weather service for fetching current weather conditions."""

from datetime import datetime

import aiohttp

from app.config import settings
from app.schemas.geo import Coordinates
from app.schemas.weather import WeatherCondition


class WeatherServiceError(Exception):
    """Base class for weather service errors."""


class WeatherServiceUnavailableError(WeatherServiceError):
    """Weather service is unavailable."""


class WeatherService:
    """Service for fetching weather information from OpenWeatherMap."""

    def __init__(self):
        self._api_key = settings.OPENWEATHERMAP_API_KEY
        self._base_url = "https://api.openweathermap.org/data/2.5/weather"

        if not self._api_key:
            raise ValueError("Missing OPENWEATHERMAP_API_KEY")

    async def get_current_weather(self, coordinates: Coordinates) -> WeatherCondition:
        """Get current weather for Helsinki (default) or specified coordinates."""
        if not self._api_key:
            raise ValueError("Missing OpenWeatherMap API key")

        params = {
            "lat": str(coordinates.latitude),
            "lon": str(coordinates.longitude),
            "appid": self._api_key,
            "units": "metric",
        }
        timeout = aiohttp.ClientTimeout(total=5.0)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self._base_url, params=params, timeout=timeout) as response:
                    if response.status != 200:
                        raise WeatherServiceUnavailableError(f"{response.status} {response.reason}")

                    data = await response.json()

                    return WeatherCondition(
                        temperature=data["main"]["temp"],
                        description=data["weather"][0]["description"],
                        humidity=data["main"]["humidity"],
                        wind_speed=data["wind"].get("speed", 0.0),
                        precipitation=data.get("rain", {}).get("1h", 0.0),
                        timestamp=datetime.now(),
                    )
        except (TimeoutError, aiohttp.ClientError, KeyError) as error:
            raise WeatherServiceUnavailableError("Failed to fetch weather data") from error
