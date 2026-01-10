from app.db.database import SessionLocal
from app.models.data import SatelliteImage, WeatherRecord
from app.models.prediction import Prediction
from sqlalchemy import func

db = SessionLocal()

print("=== SATELLITE DATA ===")
sat_count = db.query(SatelliteImage).count()
print(f"Total images: {sat_count}")
if sat_count > 0:
    dates = db.query(func.min(SatelliteImage.date), func.max(SatelliteImage.date)).first()
    print(f"Date range: {dates[0]} to {dates[1]}")
    recent = db.query(SatelliteImage).order_by(SatelliteImage.date.desc()).limit(5).all()
    print(f"\nMost recent images:")
    for img in recent:
        print(f"  {img.date} - {img.region}")

print("\n=== WEATHER DATA ===")
weather_count = db.query(WeatherRecord).count()
print(f"Total records: {weather_count}")
if weather_count > 0:
    dates = db.query(func.min(WeatherRecord.date), func.max(WeatherRecord.date)).first()
    print(f"Date range: {dates[0]} to {dates[1]}")
    recent = db.query(WeatherRecord).order_by(WeatherRecord.date.desc()).limit(5).all()
    print(f"\nMost recent weather:")
    for rec in recent:
        print(f"  {rec.date} - {rec.region} - Rainfall: {rec.rainfall}, Temp: {rec.temperature}")

print("\n=== PREDICTIONS ===")
pred_count = db.query(Prediction).count()
print(f"Total predictions: {pred_count}")
if pred_count > 0:
    dates = db.query(func.min(Prediction.predicted_at), func.max(Prediction.predicted_at)).first()
    print(f"Date range: {dates[0]} to {dates[1]}")

db.close()
