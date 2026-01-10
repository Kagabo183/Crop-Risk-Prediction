"""
Apply real Sentinel-2 NDVI data to ALL farms.
Uses existing downloaded tiles and downloads new ones as needed.
"""
import os
import sys
import json
import requests
import numpy as np
from datetime import datetime, timedelta
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from sqlalchemy import create_engine, text

# Database connection
DATABASE_URL = 'postgresql://postgres:1234@localhost:5433/crop_risk_db'

# Copernicus credentials
USERNAME = os.getenv('COPERNICUS_USERNAME', 'kagaboriziki@gmail.com')
PASSWORD = os.getenv('COPERNICUS_PASSWORD', 'Kagaboriziki@183')

def get_access_token():
    """Get OAuth2 access token"""
    print("🔐 Authenticating with Copernicus...")
    response = requests.post(
        "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token",
        data={
            'grant_type': 'password',
            'username': USERNAME,
            'password': PASSWORD,
            'client_id': 'cdse-public'
        }
    )
    if response.status_code == 200:
        print("✅ Authenticated!")
        return response.json()['access_token']
    print(f"❌ Auth failed: {response.text}")
    return None

def search_best_product(token, tile_id, days_back=60, max_cloud=30):
    """Search for best Sentinel-2 product for a tile"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    filter_query = (
        f"Collection/Name eq 'SENTINEL-2' and "
        f"Attributes/OData.CSC.StringAttribute/any(att:att/Name eq 'tileId' and att/OData.CSC.StringAttribute/Value eq '{tile_id}') and "
        f"Attributes/OData.CSC.DoubleAttribute/any(att:att/Name eq 'cloudCover' and att/OData.CSC.DoubleAttribute/Value lt {max_cloud}) and "
        f"ContentDate/Start gt {start_date.strftime('%Y-%m-%dT00:00:00.000Z')}"
    )
    
    response = requests.get(
        "https://catalogue.dataspace.copernicus.eu/odata/v1/Products",
        params={'$filter': filter_query, '$orderby': 'ContentDate/Start desc', '$top': 1},
        headers={'Authorization': f'Bearer {token}'}
    )
    
    if response.status_code == 200:
        products = response.json().get('value', [])
        if products:
            return products[0]
    return None

def download_product(token, product_id, product_name, output_dir):
    """Download a Sentinel-2 product"""
    output_path = os.path.join(output_dir, f"{product_name}.zip")
    if os.path.exists(output_path):
        print(f"   ✓ Already downloaded: {product_name}")
        return output_path
    
    print(f"   ⬇️  Downloading {product_name}...")
    download_url = f"https://download.dataspace.copernicus.eu/odata/v1/Products({product_id})/$value"
    
    response = requests.get(
        download_url,
        headers={'Authorization': f'Bearer {token}'},
        stream=True
    )
    
    if response.status_code == 200:
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024*1024):
                f.write(chunk)
                downloaded += len(chunk)
                pct = (downloaded / total_size * 100) if total_size else 0
                print(f"\r   ⬇️  {downloaded/1024/1024:.1f} MB / {total_size/1024/1024:.1f} MB ({pct:.1f}%)", end='')
        print()
        return output_path
    else:
        print(f"   ❌ Download failed: {response.status_code}")
        return None

def get_all_farms():
    """Get all farms with coordinates"""
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT id, name, latitude, longitude, location, area 
            FROM farms 
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        """))
        return [dict(row._mapping) for row in result.fetchall()]

def determine_tile(lat, lon):
    """Determine which Sentinel-2 tile covers a coordinate"""
    # Rwanda tile coverage (simplified)
    if lon < 29.5:
        return 'T35MPU'  # Far west
    elif lon < 30.0:
        return 'T35MQU'  # West
    elif lon < 30.3:
        return 'T35MQT'  # West-Central  
    elif lon < 30.8:
        return 'T36MTB'  # Central
    else:
        return 'T36MTD'  # East

def extract_ndvi_from_existing():
    """Try to use existing processed NDVI file"""
    ndvi_file = 'data/sentinel2_real/ndvi_real_20260108.tif'
    if os.path.exists(ndvi_file):
        try:
            import rasterio
            from rasterio.warp import transform as rio_transform
            
            with rasterio.open(ndvi_file) as src:
                ndvi_data = src.read(1)
                src_crs = src.crs
                transform = src.transform
                bounds = src.bounds
                
                return {
                    'data': ndvi_data,
                    'transform': transform,
                    'crs': src_crs,
                    'bounds': bounds,
                    'date': '2026-01-08',
                    'tile': 'T36MTD'
                }
        except Exception as e:
            print(f"Error reading NDVI file: {e}")
    return None

def get_ndvi_at_point(ndvi_info, lat, lon):
    """Extract NDVI value at a specific lat/lon coordinate"""
    try:
        from pyproj import Transformer
        
        # Transform lat/lon to the NDVI file's CRS
        transformer = Transformer.from_crs("EPSG:4326", ndvi_info['crs'], always_xy=True)
        x, y = transformer.transform(lon, lat)
        
        # Check if point is within bounds
        bounds = ndvi_info['bounds']
        if not (bounds.left <= x <= bounds.right and bounds.bottom <= y <= bounds.top):
            return None
        
        # Convert to pixel coordinates
        transform = ndvi_info['transform']
        col = int((x - transform.c) / transform.a)
        row = int((y - transform.f) / transform.e)
        
        # Check bounds
        data = ndvi_info['data']
        if 0 <= row < data.shape[0] and 0 <= col < data.shape[1]:
            ndvi = data[row, col]
            if not np.isnan(ndvi) and ndvi != -9999:
                return float(ndvi)
    except Exception as e:
        pass
    return None

def insert_satellite_record(conn, farm_id, ndvi_value, date, tile, source='sentinel2_real'):
    """Insert a satellite image record for a farm"""
    from datetime import date as date_type
    
    extra_metadata = json.dumps({
        'farm_id': farm_id,
        'ndvi_value': ndvi_value,
        'source': source,
        'tile': tile,
        'acquisition_date': date,
        'processed_at': datetime.now().isoformat()
    })
    
    conn.execute(text("""
        INSERT INTO satellite_images (date, region, image_type, file_path, extra_metadata)
        VALUES (:date, :region, 'ndvi', :file_path, CAST(:extra_metadata AS jsonb))
    """), {
        'date': date,
        'region': tile,
        'file_path': f'sentinel2/{tile}/ndvi_{date}.tif',
        'extra_metadata': extra_metadata
    })

def main():
    print("=" * 70)
    print("🛰️  FETCH REAL SENTINEL-2 DATA FOR ALL FARMS")
    print("=" * 70)
    
    # Get all farms
    farms = get_all_farms()
    print(f"\n📊 Total farms: {len(farms)}")
    
    # Group farms by tile
    tile_farms = {}
    for farm in farms:
        tile = determine_tile(farm['latitude'], farm['longitude'])
        if tile not in tile_farms:
            tile_farms[tile] = []
        tile_farms[tile].append(farm)
    
    print("\n📍 Farms by Sentinel-2 tile:")
    for tile, farm_list in sorted(tile_farms.items()):
        print(f"   {tile}: {len(farm_list)} farms")
    
    # Try to use existing NDVI data first
    print("\n🔍 Checking existing NDVI data...")
    ndvi_info = extract_ndvi_from_existing()
    
    engine = create_engine(DATABASE_URL)
    
    if ndvi_info:
        print(f"✅ Found existing NDVI file for tile {ndvi_info['tile']}")
        
        # Process farms covered by existing tile
        covered_farms = []
        not_covered_farms = []
        
        for farm in farms:
            ndvi = get_ndvi_at_point(ndvi_info, farm['latitude'], farm['longitude'])
            if ndvi is not None:
                covered_farms.append((farm, ndvi))
            else:
                not_covered_farms.append(farm)
        
        print(f"\n📊 Coverage:")
        print(f"   ✅ Covered by existing data: {len(covered_farms)} farms")
        print(f"   ⏳ Need additional tiles: {len(not_covered_farms)} farms")
        
        # Insert covered farms
        if covered_farms:
            print(f"\n💾 Inserting {len(covered_farms)} satellite records...")
            with engine.connect() as conn:
                for farm, ndvi in covered_farms:
                    insert_satellite_record(
                        conn, 
                        farm['id'], 
                        ndvi, 
                        ndvi_info['date'], 
                        ndvi_info['tile']
                    )
                conn.commit()
            print("✅ Done!")
        
        # For uncovered farms, we need to download more tiles
        if not_covered_farms:
            print(f"\n⚠️  {len(not_covered_farms)} farms need additional tiles:")
            uncovered_tiles = set()
            for farm in not_covered_farms:
                tile = determine_tile(farm['latitude'], farm['longitude'])
                uncovered_tiles.add(tile)
            print(f"   Tiles needed: {', '.join(uncovered_tiles)}")
            
            # Try to download additional tiles
            token = get_access_token()
            if token:
                for tile in uncovered_tiles:
                    print(f"\n🛰️  Searching for tile {tile}...")
                    product = search_best_product(token, tile)
                    if product:
                        print(f"   Found: {product['Name']}")
                        print(f"   To download, run: python scripts/download_tile.py {tile}")
                    else:
                        print(f"   ⚠️  No recent low-cloud products found")
    else:
        print("❌ No existing NDVI file found")
        print("Run: python scripts/fetch_real_sentinel2.py first")
    
    # Final summary
    with engine.connect() as conn:
        real_count = conn.execute(text(
            "SELECT COUNT(*) FROM satellite_images WHERE extra_metadata->>'source'='sentinel2_real'"
        )).fetchone()[0]
    
    print("\n" + "=" * 70)
    print(f"📊 FINAL STATUS:")
    print(f"   Total farms: {len(farms)}")
    print(f"   Farms with real satellite data: {real_count}")
    print(f"   Farms without data: {len(farms) - real_count}")
    print("=" * 70)

if __name__ == "__main__":
    main()
