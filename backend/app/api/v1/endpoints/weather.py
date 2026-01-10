from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Dict, Any
from app.services.weather_service import WeatherDataIntegrator
from datetime import datetime

router = APIRouter()

@router.get("/forecast", response_model=Dict[str, Any])
async def get_weather_forecast(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    days: int = Query(7, description="Number of days to forecast (max 14)"),
):
    """
    Get detailed weather forecast including:
    - Current conditions
    - Hourly forecast (next 24h)
    - Daily forecast (next 7 days)
    """
    try:
        weather_service = WeatherDataIntegrator()
        forecast = weather_service.get_forecast(lat=lat, lon=lon, days=days)
        
        if "error" in forecast:
            raise HTTPException(status_code=503, detail=forecast["error"])
            
        return forecast
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
