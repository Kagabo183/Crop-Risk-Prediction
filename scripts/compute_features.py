"""
Pipeline script to compute NDVI trend, anomaly, and climate features for Rwanda from ingested data.
This script demonstrates how to fetch data from the database and apply feature engineering functions.
"""
import os
import sys
from datetime import date, timedelta
import numpy as np

# Ensure the app directory is in the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.database import SessionLocal
from app.models.data import SatelliteImage, WeatherRecord

# Import the actual compute_features function from your ML module
from app.ml.feature_engineering.compute import compute_features as compute_features_fn

def compute_features(region: str, start_date: date, end_date: date):
    # Example placeholder: call the real compute_features function
    return compute_features_fn(region, start_date, end_date)

if __name__ == "__main__":
    region = "Rwanda"
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    features = compute_features(region, start_date, end_date)
    print(f"Computed features for {region} ({start_date} to {end_date}):\n{features}")
