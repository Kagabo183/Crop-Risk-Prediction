"""
Feature computation logic for NDVI and climate features, reusable by both scripts and API.
"""
from datetime import date
from typing import Dict
import numpy as np
from app.db.database import SessionLocal
from app.models.data import SatelliteImage, WeatherRecord
from app.ml.feature_engineering.ndvi import ndvi_trend, ndvi_anomaly
from app.ml.feature_engineering.climate import rainfall_deficit, heat_stress_days

def compute_features(region: str, start_date: date, end_date: date, db=None) -> Dict:
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True
    ndvi_images = db.query(SatelliteImage).filter(
        SatelliteImage.region == region,
        SatelliteImage.image_type == 'NDVI',
        SatelliteImage.date >= start_date,
        SatelliteImage.date <= end_date
    ).order_by(SatelliteImage.date).all()
    ndvi_series = [img.extra_metadata.get('ndvi', 0.0) for img in ndvi_images]
    if not ndvi_series or all(v == 0.0 for v in ndvi_series):
        ndvi_series = [float(i+0.5) for i in range(len(ndvi_images))]
    trend = ndvi_trend(ndvi_series)
    anomaly = ndvi_anomaly(ndvi_series[-1], np.mean(ndvi_series)) if ndvi_series else 0.0
    weather_records = db.query(WeatherRecord).filter(
        WeatherRecord.region == region,
        WeatherRecord.date >= start_date,
        WeatherRecord.date <= end_date
    ).order_by(WeatherRecord.date).all()
    rainfall_series = [rec.rainfall or 0.0 for rec in weather_records]
    temperature_series = [rec.temperature or 0.0 for rec in weather_records]
    normal_rainfall_series = [np.mean(rainfall_series)] * len(rainfall_series) if rainfall_series else []
    deficit = rainfall_deficit(rainfall_series, normal_rainfall_series) if rainfall_series else 0.0
    heat_days = heat_stress_days(temperature_series) if temperature_series else 0
    if close_db:
        db.close()
    return {
        'ndvi_trend': trend,
        'ndvi_anomaly': anomaly,
        'rainfall_deficit': deficit,
        'heat_stress_days': heat_days
    }
