from fastapi import APIRouter, HTTPException, status

from app.models.schemas import WeatherResponse
from app.services.weather_service import weather_service
from app.utils.geo import validate_monsoon_region

router = APIRouter(prefix="/weather", tags=["weather"])


@router.get("/{lat}/{lng}", response_model=WeatherResponse)
async def get_weather(lat: float, lng: float) -> WeatherResponse:
    if not validate_monsoon_region(lat, lng):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Location appears outside the supported Indian monsoon region.")
    return await weather_service.forecast(lat, lng)
