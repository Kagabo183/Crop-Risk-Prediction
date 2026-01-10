"""
Apply Real Sentinel-2 NDVI data to the database
Updates satellite_images and farm NDVI values from real satellite data
"""
import os
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import rasterio
from rasterio.warp import transform as warp_transform
import numpy as np
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, Text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.dialects.postgresql import JSONB

# Database connection
DATABASE_URL = "postgresql://postgres:1234@localhost:5433/crop_risk_db"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

Base = declarative_base()

class Farm(Base):
    __tablename__ = "farms"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    location = Column(String)
    area = Column(Float)
    owner_id = Column(Integer)
    latitude = Column(Float)
    longitude = Column(Float)

class SatelliteImage(Base):
    __tablename__ = "satellite_images"
    id = Column(Integer, primary_key=True)
    date = Column(Date)
    region = Column(String)
    image_type = Column(String)
    file_path = Column(String)
    extra_metadata = Column(JSONB)


def apply_real_ndvi_to_database():
    """Extract NDVI from real Sentinel-2 and update database"""
    
    print("=" * 60)
    print("🛰️  APPLYING REAL SENTINEL-2 NDVI TO DATABASE")
    print("=" * 60)
    
    # Path to real NDVI file
    ndvi_path = Path(__file__).parent.parent / "data" / "sentinel2_real" / "ndvi_real_20260108.tif"
    
    if not ndvi_path.exists():
        print(f"❌ NDVI file not found: {ndvi_path}")
        print("   Run process_real_sentinel2.py first to generate NDVI")
        return
    
    print(f"\n📂 Loading NDVI from: {ndvi_path.name}")
    
    with rasterio.open(ndvi_path) as src:
        ndvi = src.read(1)
        transform = src.transform
        crs = src.crs
        bounds = src.bounds
        
        # Convert bounds to WGS84
        from rasterio.warp import transform_bounds
        bounds_wgs84 = transform_bounds(crs, "EPSG:4326", *bounds)
        
        print(f"   Size: {src.width} x {src.height}")
        print(f"   Coverage: Lat {bounds_wgs84[1]:.2f} to {bounds_wgs84[3]:.2f}")
        print(f"   Coverage: Lon {bounds_wgs84[0]:.2f} to {bounds_wgs84[2]:.2f}")
    
    # Connect to database
    db = Session()
    
    # Get all farms
    farms = db.query(Farm).filter(
        Farm.latitude.isnot(None), 
        Farm.longitude.isnot(None)
    ).all()
    
    print(f"\n📍 Processing {len(farms)} farms...")
    
    height, width = ndvi.shape
    updated_count = 0
    skipped_count = 0
    
    for farm in farms:
        # Check if farm is within tile bounds
        if not (bounds_wgs84[0] <= farm.longitude <= bounds_wgs84[2] and
                bounds_wgs84[1] <= farm.latitude <= bounds_wgs84[3]):
            skipped_count += 1
            continue
        
        # Transform farm coordinates to image CRS
        farm_coords = warp_transform("EPSG:4326", crs, [farm.longitude], [farm.latitude])
        x, y = farm_coords[0][0], farm_coords[1][0]
        
        # Convert to pixel coordinates
        col = int((x - transform.c) / transform.a)
        row = int((y - transform.f) / transform.e)
        
        # Check bounds
        if not (0 <= row < height and 0 <= col < width):
            skipped_count += 1
            continue
        
        # Get NDVI value (use 5x5 neighborhood average for more stable reading)
        r_start, r_end = max(0, row-2), min(height, row+3)
        c_start, c_end = max(0, col-2), min(width, col+3)
        neighborhood = ndvi[r_start:r_end, c_start:c_end]
        
        # Filter out invalid values
        valid_values = neighborhood[~np.isnan(neighborhood)]
        valid_values = valid_values[(valid_values >= -1) & (valid_values <= 1)]
        
        if len(valid_values) == 0:
            farm_ndvi = 0.0
        else:
            farm_ndvi = float(np.mean(valid_values))
        
        # Determine status
        if farm_ndvi >= 0.6:
            status = "healthy"
        elif farm_ndvi >= 0.3:
            status = "moderate"
        else:
            status = "stressed"
        
        # Create satellite image record
        sat_record = SatelliteImage(
            date=datetime(2026, 1, 8).date(),
            region=farm.location or "Rwanda",
            image_type="NDVI",
            file_path=str(ndvi_path),
            extra_metadata={
                "farm_id": farm.id,
                "ndvi_value": round(farm_ndvi, 4),
                "ndvi_status": status,
                "source": "sentinel2_real",
                "tile": "T36MTD",
                "acquisition_date": "2026-01-08",
                "cloud_cover": 17.4,
                "pixel_row": row,
                "pixel_col": col
            }
        )
        db.add(sat_record)
        updated_count += 1
        
        print(f"   ✓ {farm.name}: NDVI={farm_ndvi:.3f} ({status})")
    
    # Commit changes
    db.commit()
    
    print(f"\n" + "=" * 60)
    print(f"✅ SUMMARY")
    print(f"=" * 60)
    print(f"   📊 Farms with real NDVI: {updated_count}")
    print(f"   ⏭️  Farms outside tile: {skipped_count}")
    print(f"   📅 Data date: 2026-01-08")
    print(f"   🛰️  Source: Sentinel-2 (T36MTD)")
    
    db.close()
    
    return updated_count


if __name__ == "__main__":
    apply_real_ndvi_to_database()
