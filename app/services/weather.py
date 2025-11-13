"""Weather service for fetching current weather conditions."""

from datetime import datetime

import aiohttp

from app.config import settings
from app.schemas.weather import WeatherCondition


class WeatherService:
    """Service for fetching weather information from OpenWeatherMap."""

    def __init__(self):
        self._api_key = settings.OPENWEATHERMAP_API_KEY
        self._base_url = "https://api.openweathermap.org/data/2.5/weather"

    async def get_current_weather(
        self, lat: float = 60.1695, lon: float = 24.9354
    ) -> WeatherCondition | None:
        """Get current weather for Helsinki (default) or specified coordinates."""
        if not self._api_key:
            # Return mock data if no API key is configured
            return WeatherCondition(
                temperature=12.0,
                description="partly cloudy",
                humidity=65,
                wind_speed=3.5,
                precipitation=0.0,
                timestamp=datetime.now(),
            )

        params = {"lat": str(lat), "lon": str(lon), "appid": self._api_key, "units": "metric"}
        timeout = aiohttp.ClientTimeout(total=5.0)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self._base_url, params=params, timeout=timeout) as response:
                    if response.status != 200:
                        return None

                    data = await response.json()

                    return WeatherCondition(
                        temperature=data["main"]["temp"],
                        description=data["weather"][0]["description"],
                        humidity=data["main"]["humidity"],
                        wind_speed=data["wind"].get("speed", 0.0),
                        precipitation=data.get("rain", {}).get("1h", 0.0),
                        timestamp=datetime.now(),
                    )
        except (TimeoutError, aiohttp.ClientError, KeyError):
            return None
