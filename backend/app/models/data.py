from sqlalchemy import Column, Integer, String, Float, Date, DateTime, JSON
from app.db.database import Base

class SatelliteImage(Base):
    __tablename__ = "satellite_images"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    region = Column(String, nullable=False)
    image_type = Column(String, nullable=False)  # e.g., 'NDVI', 'EVI', 'RGB'
    file_path = Column(String, nullable=False)  # Path to stored image file
    extra_metadata = Column(JSON, nullable=True)  # Any extra info (cloud cover, etc.)

class WeatherRecord(Base):
    __tablename__ = "weather_records"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    region = Column(String, nullable=False)
    rainfall = Column(Float, nullable=True)  # mm
    temperature = Column(Float, nullable=True)  # °C
    drought_index = Column(Float, nullable=True)  # SPI or similar
    source = Column(String, nullable=False)  # e.g., 'CHIRPS', 'ERA5'
    extra_metadata = Column(JSON, nullable=True)
