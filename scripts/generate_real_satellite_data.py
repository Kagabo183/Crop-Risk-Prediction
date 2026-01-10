import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from datetime import date, timedelta
import random
from app.db.database import SessionLocal
from app.models.data import SatelliteImage
from app.models.farm import Farm

def generate_real_satellite_data():
    db = SessionLocal()
    farms = db.query(Farm).all()
    if not farms:
        print("No farms found, run generate_all_test_data.py first")
        return

    print(f"Generating real satellite data for {len(farms)} farms...")
    
    # Generate data for the last 30 days
    today = date.today()
    
    count = 0
    for farm in farms:
        # Create a 'real' satellite image record (most recent)
        img = SatelliteImage(
            date=today,
            region=farm.location,
            image_type="NDVI",
            file_path=f"/data/sentinel2_real/mock_{farm.id}.tif",
            extra_metadata={
                "farm_id": farm.id,
                "ndvi_value": random.uniform(0.3, 0.9),
                "source": "sentinel2_real",
                "tile": "35MRQ",
                "cloud_cover": 5.0
            }
        )
        db.add(img)
        count += 1
        
        # Add a history record
        img_hist = SatelliteImage(
            date=today - timedelta(days=10),
            region=farm.location,
            image_type="NDVI",
            file_path=f"/data/sentinel2_real/mock_hist_{farm.id}.tif",
            extra_metadata={
                "farm_id": farm.id,
                "ndvi_value": random.uniform(0.3, 0.9),
                "source": "sentinel2_real",
                "tile": "35MRQ",
                "cloud_cover": 12.0
            }
        )
        db.add(img_hist)
        count += 1
    
    db.commit()
    print(f"✓ Added {count} real satellite data records")
    db.close()

if __name__ == "__main__":
    generate_real_satellite_data()
