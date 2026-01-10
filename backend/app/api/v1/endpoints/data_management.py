"""API endpoint to manually trigger data fetching.

Note: The backend Docker image is built from ./backend, so repo-root scripts
like scripts/auto_fetch_data.py are NOT available inside the container.
We trigger the in-container Celery task instead.
"""

from fastapi import APIRouter
from typing import Dict


router = APIRouter()


@router.post("/fetch-data", response_model=Dict)
async def trigger_data_fetch():
    """Manually trigger data fetching for satellite and weather data."""
    from app.tasks.process_tasks import auto_fetch_daily_data

    # Enqueue Celery task so it runs in the worker container.
    task = auto_fetch_daily_data.delay()

    return {
        "status": "success",
        "message": "Data fetch queued. Weather/Satellite records will update shortly.",
        "task_id": task.id,
    }

@router.get("/data-status", response_model=Dict)
async def get_data_status():
    """
    Get current status of data in the database.
    Shows counts and date ranges for satellite, weather, and prediction data.
    """
    from app.db.database import SessionLocal
    from app.models.data import SatelliteImage, WeatherRecord
    from app.models.prediction import Prediction
    from sqlalchemy import func
    from datetime import date
    
    db = SessionLocal()
    
    try:
        # Satellite data
        sat_count = db.query(SatelliteImage).count()
        sat_dates = db.query(
            func.min(SatelliteImage.date), 
            func.max(SatelliteImage.date)
        ).first() if sat_count > 0 else (None, None)
        
        # Weather data
        weather_count = db.query(WeatherRecord).count()
        weather_dates = db.query(
            func.min(WeatherRecord.date), 
            func.max(WeatherRecord.date)
        ).first() if weather_count > 0 else (None, None)
        
        # Predictions
        pred_count = db.query(Prediction).count()
        pred_dates = db.query(
            func.min(Prediction.predicted_at), 
            func.max(Prediction.predicted_at)
        ).first() if pred_count > 0 else (None, None)
        
        today = date.today()
        
        return {
            "status": "success",
            "current_date": str(today),
            "satellite_data": {
                "count": sat_count,
                "earliest_date": str(sat_dates[0]) if sat_dates[0] else None,
                "latest_date": str(sat_dates[1]) if sat_dates[1] else None,
                "days_behind": (today - sat_dates[1]).days if sat_dates[1] else None,
                "up_to_date": sat_dates[1] >= today if sat_dates[1] else False
            },
            "weather_data": {
                "count": weather_count,
                "earliest_date": str(weather_dates[0]) if weather_dates[0] else None,
                "latest_date": str(weather_dates[1]) if weather_dates[1] else None,
                "days_behind": (today - weather_dates[1]).days if weather_dates[1] else None,
                "up_to_date": weather_dates[1] >= today if weather_dates[1] else False
            },
            "predictions": {
                "count": pred_count,
                "earliest": str(pred_dates[0]) if pred_dates[0] else None,
                "latest": str(pred_dates[1]) if pred_dates[1] else None
            }
        }
    finally:
        db.close()
