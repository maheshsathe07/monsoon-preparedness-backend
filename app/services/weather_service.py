from __future__ import annotations

from datetime import datetime, timedelta, timezone

import httpx

from app.models.schemas import WeatherResponse


class WeatherService:
    def __init__(self) -> None:
        self._cache: dict[str, tuple[datetime, WeatherResponse]] = {}

    async def forecast(self, lat: float, lng: float) -> WeatherResponse:
        key = f"{lat:.3f}:{lng:.3f}"
        cached = self._cache.get(key)
        if cached and cached[0] > datetime.now(timezone.utc):
            return cached[1]
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lng,
            "daily": "precipitation_sum",
            "forecast_days": 7,
            "timezone": "auto",
        }
        rainfall = [0.0] * 7
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                rainfall = [float(value or 0) for value in response.json().get("daily", {}).get("precipitation_sum", rainfall)]
        except httpx.HTTPError:
            rainfall = [0.0] * 7
        max_rain = max(rainfall) if rainfall else 0.0
        if max_rain > 60:
            level = "RED"
        elif max_rain >= 20:
            level = "YELLOW"
        else:
            level = "GREEN"
        result = WeatherResponse(
            lat=lat,
            lng=lng,
            daily_rainfall_mm=rainfall,
            max_rainfall_mm=max_rain,
            monsoon_alert_level=level,
            summary=f"Highest expected daily rainfall is {max_rain:.1f} mm. Alert level: {level}.",
        )
        self._cache[key] = (datetime.now(timezone.utc) + timedelta(hours=6), result)
        return result


weather_service = WeatherService()
