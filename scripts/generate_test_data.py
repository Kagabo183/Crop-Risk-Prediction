"""
Enhanced script to generate 1000+ mock Sentinel-2 records with actual TIFF files.
Creates dummy geospatial NDVI data for testing the auto-processing pipeline at scale.
"""

import os
import sys
from datetime import date
from sqlalchemy.orm import Session
from pathlib import Path

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

def generate_mock_data(count=1000, create_files=True):
    """Generate mock records and optionally create dummy TIFF files.
    
    Args:
        count: number of records to generate
        create_files: if True and rasterio available, create actual TIFF files with random NDVI data
    """
    import random
    records = []
    data_dir = Path("data/sentinel2")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Generating {count} mock satellite records...")
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
                    
                if (i + 1) % 100 == 0:
                    print(f"  Created {i+1}/{count} TIFF files...")
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
    """Insert records into database."""
    db: Session = SessionLocal()
    try:
        print(f"Inserting {len(records)} records into database...")
        for i, rec in enumerate(records):
            img = SatelliteImage(**rec)
            db.add(img)
            if (i + 1) % 500 == 0:
                db.commit()
                print(f"  Committed {i+1}/{len(records)} records...")
        db.commit()
        print(f"✓ Stored {len(records)} Sentinel-2 image records in DB.")
    except Exception as e:
        db.rollback()
        print(f"✗ Error storing records: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Generate mock Sentinel-2 data at scale')
    parser.add_argument('--count', type=int, default=1000, help='Number of records to generate (default: 1000)')
    parser.add_argument('--no-files', action='store_true', help='Skip creating TIFF files (DB records only)')
    args = parser.parse_args()
    
    records = generate_mock_data(count=args.count, create_files=not args.no_files)
    store_satellite_images(records)
    
    print(f"\n{'='*60}")
    print(f"✓ Generated {args.count} records")
    print(f"✓ TIFF files: {'created' if not args.no_files and HAS_RASTERIO else 'skipped'}")
    print(f"{'='*60}")
    print("\nNext steps to process NDVI:")
    print("  1. Trigger auto-scan via API:")
    print("     curl -X GET http://127.0.0.1:8000/api/v1/satellite-images/scan")
    print("\n  2. Or run batch processor:")
    print("     python scripts/batch_process_ndvi.py")
    print("\n  3. Monitor worker progress:")
    print("     docker compose logs -f worker")
    print("\n  4. Check results:")
    print("     curl http://127.0.0.1:8000/api/v1/satellite-images/ndvi-means")
