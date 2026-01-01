import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.farm import Farm

# Rwanda district coordinates (approximate centers)
RWANDA_LOCATIONS = {
    "Nyagatare": {"lat": -1.2967, "lng": 30.3314},
    "Musanze": {"lat": -1.4989, "lng": 29.6368},
    "Rusizi": {"lat": -2.4793, "lng": 28.9097},
    "Rulindo": {"lat": -1.7833, "lng": 30.0500},
    "Bugesera": {"lat": -2.2167, "lng": 30.2000},
    "Kayonza": {"lat": -1.8833, "lng": 30.5833},
    "Huye": {"lat": -2.5971, "lng": 29.7390},
    "Karongi": {"lat": -2.0000, "lng": 29.3833},
}

def add_coordinates_to_farms():
    """Add latitude and longitude to farms based on their location"""
    db: Session = SessionLocal()
    
    try:
        farms = db.query(Farm).all()
        print(f"Found {len(farms)} farms")
        
        updated = 0
        for farm in farms:
            # Extract district from location
            if farm.location:
                parts = farm.location.split(",")
                district = parts[0].strip()
                
                # Find matching coordinates
                coords = RWANDA_LOCATIONS.get(district)
                if coords:
                    # Add slight random offset so farms don't overlap (±0.05 degrees ~ 5km)
                    import random
                    farm.latitude = coords["lat"] + random.uniform(-0.05, 0.05)
                    farm.longitude = coords["lng"] + random.uniform(-0.05, 0.05)
                    updated += 1
                    print(f"✓ Updated {farm.name}: {farm.latitude:.4f}, {farm.longitude:.4f}")
                else:
                    print(f"⚠ No coordinates for district: {district}")
        
        db.commit()
        print(f"\n✅ Successfully updated {updated} farms with coordinates")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_coordinates_to_farms()
