"""
Script to fetch Sentinel-2 NDVI/EVI data for Rwanda and store metadata in the database.
This is a scaffold; real implementation will require authentication and API usage (e.g., Copernicus Open Access Hub, Google Earth Engine, or AWS Open Data).
"""

import os
import sys
from datetime import date
from sqlalchemy.orm import Session
from pathlib import Path

# Ensure the app directory is in the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.database import SessionLocal
from app.models.data import SatelliteImage

try:
    import numpy as np
    import rasterio
    from rasterio.transform import from_bounds
    HAS_RASTERIO = True
except ImportError:
    HAS_RASTERIO = False
    print("Warning: rasterio/numpy not installed; will only create DB records, not TIFF files.")

# Example: region bounding box for Rwanda (approximate)
RWANDA_BBOX = {
    "min_lon": 28.8,
    "min_lat": -2.9,
    "max_lon": 30.9,
    "max_lat": -1.0
}

def fetch_sentinel2_metadata(count=1000, create_files=True):
    """Generate mock records and optionally create dummy TIFF files.
    
    Args:
        count: number of records to generate
        create_files: if True and rasterio available, create actual TIFF files with random NDVI data
    """
    import random
    records = []
    data_dir = Path("data/sentinel2")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    for i in range(count):
        img_type = random.choice(["NDVI", "EVI", "RGB"])
        day = random.randint(1, 28)
        month = random.randint(1, 12)
        year = 2025
        filename = f"{img_type.lower()}_{year}{month:02d}{day:02d}_{i:04d}.tif"
        file_path = f"data/sentinel2/{filename}"
        abs_path = data_dir / filename
        
        # Create dummy TIFF if requested and available
        if create_files and HAS_RASTERIO and not abs_path.exists():
            try:
                # Create a small 100x100 NDVI image with random values between -0.2 and 0.9
                height, width = 100, 100
                ndvi_data = np.random.uniform(-0.2, 0.9, (height, width)).astype('float32')
                
                # Define a simple geo transform (rough Rwanda bbox)
                transform = from_bounds(
                    RWANDA_BBOX["min_lon"], RWANDA_BBOX["min_lat"],
                    RWANDA_BBOX["max_lon"], RWANDA_BBOX["max_lat"],
                    width, height
                )
                
                with rasterio.open(
                    abs_path, 'w',
                    driver='GTiff',
                    height=height, width=width,
                    count=1, dtype='float32',
                    crs='EPSG:4326',
                    transform=transform,
                    nodata=-9999
                ) as dst:
                    dst.write(ndvi_data, 1)
            except Exception as e:
                print(f"Failed to create {filename}: {e}")
        
        records.append({
            "date": date(year, month, day),
            "region": "Rwanda",
            "image_type": img_type,
            "file_path": file_path,
            "extra_metadata": {"cloud_cover": round(random.uniform(0, 100), 2)}
        })
    return records

def store_satellite_images(records):
    db: Session = SessionLocal()
    try:
        for rec in records:
            img = SatelliteImage(**rec)
            db.add(img)
        db.commit()
        print(f"Stored {len(records)} Sentinel-2 image records in DB.")
    except Exception as e:
        db.rollback()
        print(f"Error storing records: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Generate mock Sentinel-2 data')
    parser.add_argument('--count', type=int, default=1000, help='Number of records to generate')
    parser.add_argument('--no-files', action='store_true', help='Skip creating TIFF files')
    args = parser.parse_args()
    
    records = fetch_sentinel2_metadata(count=args.count, create_files=not args.no_files)
    store_satellite_images(records)
    print(f"Generated {args.count} records. TIFF files: {'created' if not args.no_files and HAS_RASTERIO else 'skipped'}.")
