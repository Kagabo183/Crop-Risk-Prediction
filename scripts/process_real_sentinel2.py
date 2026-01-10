"""
Process Real Sentinel-2 Data
Calculate NDVI from actual satellite imagery and extract values for farms
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    import rasterio
    from rasterio.warp import transform_bounds
    import numpy as np
except ImportError:
    print("Installing required packages...")
    os.system(f"{sys.executable} -m pip install rasterio numpy")
    import rasterio
    from rasterio.warp import transform_bounds
    import numpy as np

# Paths to the band files
SENTINEL_DIR = Path(__file__).parent.parent / "data" / "sentinel2_real"
SAFE_DIR = SENTINEL_DIR / "S2C_MSIL1C_20260108T080321_N0511_R035_T36MTD_20260108T095659.SAFE"
IMG_DATA = SAFE_DIR / "GRANULE" / "L1C_T36MTD_A007012_20260108T081556" / "IMG_DATA"

B04_PATH = IMG_DATA / "T36MTD_20260108T080321_B04.jp2"  # Red band
B08_PATH = IMG_DATA / "T36MTD_20260108T080321_B08.jp2"  # NIR band


def calculate_ndvi():
    """Calculate NDVI from B04 (Red) and B08 (NIR) bands"""
    
    print("=" * 60)
    print("🛰️  PROCESSING REAL SENTINEL-2 DATA")
    print("=" * 60)
    
    if not B04_PATH.exists():
        print(f"❌ B04 file not found: {B04_PATH}")
        return
    if not B08_PATH.exists():
        print(f"❌ B08 file not found: {B08_PATH}")
        return
    
    print(f"\n📂 Reading Red band (B04): {B04_PATH.name}")
    with rasterio.open(B04_PATH) as src_red:
        red = src_red.read(1).astype(np.float32)
        red_profile = src_red.profile
        red_bounds = src_red.bounds
        red_crs = src_red.crs
        red_transform = src_red.transform
        
        print(f"   Size: {src_red.width} x {src_red.height} pixels")
        print(f"   CRS: {red_crs}")
        print(f"   Bounds (native): {red_bounds}")
        
        # Convert bounds to WGS84 lat/lon
        bounds_wgs84 = transform_bounds(red_crs, "EPSG:4326", *red_bounds)
        print(f"   Bounds (WGS84): {bounds_wgs84}")
        print(f"   Latitude range: {bounds_wgs84[1]:.4f} to {bounds_wgs84[3]:.4f}")
        print(f"   Longitude range: {bounds_wgs84[0]:.4f} to {bounds_wgs84[2]:.4f}")
    
    print(f"\n📂 Reading NIR band (B08): {B08_PATH.name}")
    with rasterio.open(B08_PATH) as src_nir:
        nir = src_nir.read(1).astype(np.float32)
        print(f"   Size: {src_nir.width} x {src_nir.height} pixels")
    
    print("\n🔬 Calculating NDVI...")
    # NDVI = (NIR - Red) / (NIR + Red)
    denominator = nir + red
    ndvi = np.where(denominator > 0, (nir - red) / denominator, 0)
    
    # Clip to valid NDVI range
    ndvi = np.clip(ndvi, -1, 1)
    
    print(f"   NDVI range: {ndvi.min():.3f} to {ndvi.max():.3f}")
    print(f"   Mean NDVI: {ndvi.mean():.3f}")
    
    # Save NDVI as GeoTIFF
    output_path = SENTINEL_DIR / "ndvi_real_20260108.tif"
    
    ndvi_profile = red_profile.copy()
    ndvi_profile.update(
        dtype=rasterio.float32,
        count=1,
        driver='GTiff',
        compress='lzw'
    )
    
    print(f"\n💾 Saving NDVI to: {output_path}")
    with rasterio.open(output_path, 'w', **ndvi_profile) as dst:
        dst.write(ndvi.astype(np.float32), 1)
    
    print("✅ NDVI saved successfully!")
    
    return ndvi, red_transform, red_crs, bounds_wgs84


def extract_farm_ndvi_values(ndvi, transform, crs):
    """Extract NDVI values for each farm based on their coordinates"""
    from rasterio.warp import transform as warp_transform
    from sqlalchemy import create_engine, Column, Integer, String, Float
    from sqlalchemy.orm import sessionmaker, declarative_base
    
    # Connect to PostgreSQL database
    DATABASE_URL = "postgresql://postgres:1234@localhost:5433/crop_risk_db"
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    # Define Farm model locally to avoid config issues
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
    
    print("\n" + "=" * 60)
    print("🌾 EXTRACTING NDVI VALUES FOR FARMS")
    print("=" * 60)
    farms = db.query(Farm).filter(Farm.latitude.isnot(None), Farm.longitude.isnot(None)).all()
    
    print(f"\n📍 Found {len(farms)} farms with coordinates")
    
    # Get NDVI dimensions
    height, width = ndvi.shape
    
    results = []
    for farm in farms:
        # Transform farm coordinates from WGS84 to image CRS
        farm_coords = warp_transform("EPSG:4326", crs, [farm.longitude], [farm.latitude])
        x, y = farm_coords[0][0], farm_coords[1][0]
        
        # Convert to pixel coordinates
        col = int((x - transform.c) / transform.a)
        row = int((y - transform.f) / transform.e)
        
        # Check if within image bounds
        if 0 <= row < height and 0 <= col < width:
            farm_ndvi = ndvi[row, col]
            
            # Get neighborhood average (5x5 window)
            r_start, r_end = max(0, row-2), min(height, row+3)
            c_start, c_end = max(0, col-2), min(width, col+3)
            neighborhood_ndvi = ndvi[r_start:r_end, c_start:c_end].mean()
            
            status = "healthy" if farm_ndvi > 0.6 else "moderate" if farm_ndvi > 0.3 else "stressed"
            
            results.append({
                "farm_id": farm.id,
                "name": farm.name,
                "latitude": farm.latitude,
                "longitude": farm.longitude,
                "ndvi": float(farm_ndvi),
                "ndvi_avg": float(neighborhood_ndvi),
                "status": status
            })
            
            print(f"   ✓ {farm.name}: NDVI={farm_ndvi:.3f} ({status})")
        else:
            print(f"   ⚠ {farm.name}: Outside image bounds (lat={farm.latitude:.4f}, lon={farm.longitude:.4f})")
    
    db.close()
    
    print(f"\n✅ Extracted NDVI for {len(results)} farms")
    return results


def main():
    # Calculate NDVI
    result = calculate_ndvi()
    
    if result:
        ndvi, transform, crs, bounds = result
        
        # Check if farms are within this tile's bounds
        print("\n📊 Tile Coverage Analysis:")
        print(f"   This tile covers: {bounds[1]:.2f}°S to {bounds[3]:.2f}°S latitude")
        print(f"                     {bounds[0]:.2f}°E to {bounds[2]:.2f}°E longitude")
        
        # Try to extract farm values
        try:
            os.environ.setdefault("DATABASE_URL", "sqlite:///./crop_risk.db")
            os.environ.setdefault("SECRET_KEY", "dev-secret-key")
            results = extract_farm_ndvi_values(ndvi, transform, crs)
            
            if results:
                print("\n" + "=" * 60)
                print("📈 FARM NDVI SUMMARY")
                print("=" * 60)
                healthy = sum(1 for r in results if r["status"] == "healthy")
                moderate = sum(1 for r in results if r["status"] == "moderate")
                stressed = sum(1 for r in results if r["status"] == "stressed")
                print(f"   🟢 Healthy (NDVI > 0.6): {healthy} farms")
                print(f"   🟡 Moderate (0.3-0.6):   {moderate} farms")
                print(f"   🔴 Stressed (< 0.3):     {stressed} farms")
        except Exception as e:
            print(f"\n⚠️  Could not extract farm values: {e}")
            print("   (This may happen if farms are outside this tile's coverage)")


if __name__ == "__main__":
    main()
