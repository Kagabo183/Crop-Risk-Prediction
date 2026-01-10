import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.database import SessionLocal
from app.models.farm import Farm

# Rwanda bounds (strict)
RWANDA_BOUNDS = {
    "min_lat": -2.84,
    "max_lat": -1.05,
    "min_lng": 28.86,
    "max_lng": 30.90
}

def check_farms():
    db = SessionLocal()
    farms = db.query(Farm).all()
    
    print(f"Total farms: {len(farms)}\n")
    print("=" * 80)
    
    outside_rwanda = []
    inside_rwanda = []
    no_coords = []
    
    for farm in farms:
        if farm.latitude is None or farm.longitude is None:
            no_coords.append(farm)
            continue
            
        # Check if within Rwanda bounds
        in_rwanda = (
            RWANDA_BOUNDS["min_lat"] <= farm.latitude <= RWANDA_BOUNDS["max_lat"] and
            RWANDA_BOUNDS["min_lng"] <= farm.longitude <= RWANDA_BOUNDS["max_lng"]
        )
        
        if in_rwanda:
            inside_rwanda.append(farm)
        else:
            outside_rwanda.append(farm)
    
    print(f"\n✅ Farms INSIDE Rwanda: {len(inside_rwanda)}")
    for f in inside_rwanda[:5]:  # Show first 5
        print(f"   {f.name}: ({f.latitude:.4f}, {f.longitude:.4f}) - {f.location}")
    
    print(f"\n❌ Farms OUTSIDE Rwanda (DRC/Tanzania/etc): {len(outside_rwanda)}")
    for f in outside_rwanda:
        print(f"   ID:{f.id} {f.name}: ({f.latitude:.4f}, {f.longitude:.4f}) - {f.location}")
    
    print(f"\n⚠️  Farms with NO coordinates: {len(no_coords)}")
    for f in no_coords:
        print(f"   ID:{f.id} {f.name} - {f.location}")
    
    db.close()
    return outside_rwanda, no_coords

if __name__ == "__main__":
    check_farms()
