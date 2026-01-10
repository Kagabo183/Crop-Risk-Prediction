"""Apply all downloaded NDVI tiles to all farms."""
import os
import rasterio
import numpy as np
from pyproj import Transformer
from sqlalchemy import create_engine, text
from datetime import datetime

DB_URL = "postgresql://postgres:1234@localhost:5433/crop_risk_db"
NDVI_DIR = "data/sentinel2_real"


def main():
    engine = create_engine(DB_URL)
    
    # Get all farms with coordinates
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT id, name, latitude, longitude FROM farms
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        """))
        farms = [(row[0], row[1], row[2], row[3]) for row in result.fetchall()]
    
    print(f"Total farms with coordinates: {len(farms)}")
    
    # Find all NDVI tiles
    ndvi_files = [f for f in os.listdir(NDVI_DIR) if f.startswith("ndvi_T") and f.endswith(".tif")]
    print(f"NDVI tiles available: {len(ndvi_files)}")
    for f in ndvi_files:
        print(f"  - {f}")
    
    # Clear existing real records to avoid duplicates
    with engine.connect() as conn:
        result = conn.execute(text("""
            DELETE FROM satellite_images
            WHERE extra_metadata->>'source' = 'copernicus_sentinel2'
        """))
        conn.commit()
        print(f"\nCleared existing real records")
    
    # Track which farms have been processed
    farms_processed = set()
    total_records = 0
    
    for ndvi_file in ndvi_files:
        tile_id = ndvi_file.replace("ndvi_", "").replace(".tif", "")
        ndvi_path = os.path.join(NDVI_DIR, ndvi_file)
        
        print(f"\n{'='*50}")
        print(f"Processing tile: {tile_id}")
        print('='*50)
        
        try:
            with rasterio.open(ndvi_path) as src:
                ndvi = src.read(1)
                src_crs = src.crs
                
                # Create transformer from WGS84 to tile CRS
                transformer = Transformer.from_crs("EPSG:4326", src_crs, always_xy=True)
                
                farms_added = 0
                for farm_id, name, lat, lon in farms:
                    if farm_id in farms_processed:
                        continue  # Skip already processed farms
                    
                    # Transform farm coordinates to tile CRS
                    x, y = transformer.transform(lon, lat)
                    
                    # Get pixel coordinates
                    try:
                        row, col = src.index(x, y)
                    except Exception:
                        continue  # Outside bounds
                    
                    # Check bounds
                    if 0 <= row < ndvi.shape[0] and 0 <= col < ndvi.shape[1]:
                        # Get 5x5 window around farm
                        r_min = max(0, row - 2)
                        r_max = min(ndvi.shape[0], row + 3)
                        c_min = max(0, col - 2)
                        c_max = min(ndvi.shape[1], col + 3)
                        
                        ndvi_window = ndvi[r_min:r_max, c_min:c_max]
                        ndvi_mean = float(np.nanmean(ndvi_window))
                        
                        if np.isnan(ndvi_mean) or ndvi_mean < -1 or ndvi_mean > 1:
                            continue  # Invalid NDVI value
                        
                        # Insert record
                        with engine.connect() as conn:
                            conn.execute(text("""
                                INSERT INTO satellite_images (date, region, image_type, file_path, extra_metadata)
                                VALUES (:date, :region, 'ndvi', :path, :meta)
                            """), {
                                "date": datetime.now().date(),
                                "region": f"farm_{farm_id}",
                                "path": ndvi_path,
                                "meta": f'{{"source": "copernicus_sentinel2", "farm_id": {farm_id}, "ndvi_mean": {ndvi_mean:.4f}, "tile": "{tile_id}", "cloud_cover": 5.0}}'
                            })
                            conn.commit()
                        
                        farms_processed.add(farm_id)
                        farms_added += 1
                        total_records += 1
                        print(f"  ✅ Farm {farm_id}: {name} -> NDVI = {ndvi_mean:.4f}")
                
                print(f"  Added {farms_added} farms from tile {tile_id}")
                
        except Exception as e:
            print(f"  Error processing {tile_id}: {e}")
            continue
    
    print(f"\n{'='*50}")
    print(f"SUMMARY")
    print('='*50)
    print(f"Total records inserted: {total_records}")
    print(f"Farms with real data: {len(farms_processed)}/{len(farms)}")
    
    # List farms still missing
    missing_farms = [f for f in farms if f[0] not in farms_processed]
    if missing_farms:
        print(f"\nFarms still missing real data: {len(missing_farms)}")
        for farm_id, name, lat, lon in missing_farms:
            print(f"  ID {farm_id}: {name} ({lat}, {lon})")
    else:
        print("\n✅ ALL FARMS HAVE REAL SATELLITE DATA!")


if __name__ == "__main__":
    main()
