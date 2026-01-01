"""
Script to fetch CHIRPS/ERA5 weather data for Rwanda and store in the database.
This is a scaffold; real implementation will require API or file access to CHIRPS/ERA5 datasets.
"""
import os
import sys
from datetime import date
from sqlalchemy.orm import Session

# Ensure the app directory is in the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.database import SessionLocal
from app.models.data import WeatherRecord

def fetch_weather_data():
    # TODO: Replace with real API/file access to CHIRPS/ERA5 for Rwanda
    # This is a mock example
    return [
        {
            "date": date(2025, 12, 20),
            "region": "Rwanda",
            "rainfall": 12.5,
            "temperature": 22.3,
            "drought_index": -0.7,
            "source": "CHIRPS",
            "extra_metadata": {"station_count": 15}
        },
        {
            "date": date(2025, 12, 20),
            "region": "Rwanda",
            "rainfall": 13.1,
            "temperature": 21.8,
            "drought_index": -0.5,
            "source": "ERA5",
            "extra_metadata": {"grid_resolution": "0.25deg"}
        }
    ]

def store_weather_records(records):
    db: Session = SessionLocal()
    for rec in records:
        record = WeatherRecord(**rec)
        db.add(record)
    db.commit()
    db.close()

if __name__ == "__main__":
    records = fetch_weather_data()
    store_weather_records(records)
    print(f"Stored {len(records)} weather records.")
