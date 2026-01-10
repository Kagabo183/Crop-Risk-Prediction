"""
Download and process ALL Sentinel-2 tiles for Rwanda farms.
This script:
1. Downloads all available tiles covering Rwanda
2. Calculates NDVI for each tile
3. Extracts NDVI values for all farms
4. Inserts real satellite data into database
"""
import os
import sys
import json
import zipfile
import requests
import numpy as np
from datetime import datetime, timedelta
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from sqlalchemy import create_engine, text

# Config
DATABASE_URL = 'postgresql://postgres:1234@localhost:5433/crop_risk_db'
USERNAME = os.getenv('COPERNICUS_USERNAME', 'kagaboriziki@gmail.com')
PASSWORD = os.getenv('COPERNICUS_PASSWORD', 'Kagaboriziki@183')
OUTPUT_DIR = 'data/sentinel2_real'

os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_access_token():
    print("🔐 Authenticating with Copernicus...")
    r = requests.post(
        'https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token',
        data={'grant_type': 'password', 'username': USERNAME, 'password': PASSWORD, 'client_id': 'cdse-public'}
    )
    if r.status_code == 200:
        print("✅ Authenticated!")
        return r.json()['access_token']
    print(f"❌ Failed: {r.text}")
    return None

def search_rwanda_products(token, days_back=30):
    """Search for all Sentinel-2 products covering Rwanda"""
    print("\n🔍 Searching for Rwanda Sentinel-2 products...")
    end = datetime.now()
    start = end - timedelta(days=days_back)
    
    polygon = "POLYGON((28.8 -2.9, 30.9 -2.9, 30.9 -1.0, 28.8 -1.0, 28.8 -2.9))"
    filter_str = f"Collection/Name eq 'SENTINEL-2' and OData.CSC.Intersects(area=geography'SRID=4326;{polygon}') and ContentDate/Start gt {start.strftime('%Y-%m-%dT00:00:00.000Z')}"
    
    r = requests.get(
        'https://catalogue.dataspace.copernicus.eu/odata/v1/Products',
        params={'$filter': filter_str, '$top': 50, '$orderby': 'ContentDate/Start desc'},
        headers={'Authorization': f'Bearer {token}'}
    )
    
    if r.status_code == 200:
        products = r.json().get('value', [])
        print(f"   Found {len(products)} products")
        return products
    print(f"   ❌ Search failed: {r.status_code}")
    return []

def get_best_products_per_tile(products):
    """Get the best (most recent L1C) product per tile"""
    tile_products = {}
    for p in products:
        name = p['Name']
        # Extract tile from name (e.g., T36MTD)
        parts = name.split('_')
        tile = None
        for part in parts:
            if part.startswith('T') and len(part) == 6:
                tile = part
                break
        
        if not tile:
            continue
            
        # Prefer L1C (we already downloaded T36MTD as L1C)
        is_l1c = 'L1C' in name
        
        if tile not in tile_products:
            tile_products[tile] = p
        elif is_l1c and 'L1C' not in tile_products[tile]['Name']:
            tile_products[tile] = p
    
    return tile_products

def download_product(token, product, output_dir):
    """Download a Sentinel-2 product"""
    product_id = product['Id']
    product_name = product['Name']
    output_path = os.path.join(output_dir, f"{product_name}.zip")
    
    if os.path.exists(output_path):
        print(f"   ✓ Already exists: {product_name[:50]}...")
        return output_path
    
    print(f"   ⬇️  Downloading {product_name[:50]}...")
    
    r = requests.get(
        f"https://download.dataspace.copernicus.eu/odata/v1/Products({product_id})/$value",
        headers={'Authorization': f'Bearer {token}'},
        stream=True
    )
    
    if r.status_code == 200:
        total = int(r.headers.get('content-length', 0))
        downloaded = 0
        with open(output_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024*1024):
                f.write(chunk)
                downloaded += len(chunk)
                if total:
                    print(f"\r      {downloaded/1024/1024:.0f}/{total/1024/1024:.0f} MB", end='')
        print(" ✅")
        return output_path
    else:
        print(f"   ❌ Download failed: {r.status_code}")
        return None

def extract_and_calculate_ndvi(zip_path, tile):
    """Extract bands and calculate NDVI"""
    import rasterio
    
    print(f"   📦 Extracting {tile}...")
    extract_dir = os.path.join(OUTPUT_DIR, tile)
    
    # Find B04 and B08 in zip
    b04_path = None
    b08_path = None
    
    with zipfile.ZipFile(zip_path, 'r') as z:
        for name in z.namelist():
            if 'B04_10m.jp2' in name or 'B04.jp2' in name:
                b04_path = z.extract(name, extract_dir)
            elif 'B08_10m.jp2' in name or 'B08.jp2' in name:
                b08_path = z.extract(name, extract_dir)
    
    if not b04_path or not b08_path:
        print(f"   ❌ Could not find B04/B08 bands")
        return None
    
    print(f"   🔢 Calculating NDVI...")
    with rasterio.open(b04_path) as b04, rasterio.open(b08_path) as b08:
        red = b04.read(1).astype(np.float32)
        nir = b08.read(1).astype(np.float32)
        
        # Avoid division by zero
        denominator = nir + red
        ndvi = np.where(denominator > 0, (nir - red) / denominator, 0)
        
        # Save NDVI as GeoTIFF (not JP2)
        ndvi_path = os.path.join(OUTPUT_DIR, f'ndvi_{tile}.tif')
        profile = b04.profile.copy()
        profile.update(
            dtype=rasterio.float32, 
            count=1,
            driver='GTiff',
            compress='lzw'
        )
        
        with rasterio.open(ndvi_path, 'w', **profile) as dst:
            dst.write(ndvi.astype(np.float32), 1)
    
    print(f"   ✅ NDVI saved: ndvi_{tile}.tif")
    
    # Re-open to return info
    with rasterio.open(ndvi_path) as src:
        return {
            'ndvi_path': ndvi_path,
            'crs': src.crs,
            'transform': src.transform,
            'bounds': src.bounds
        }

def get_all_farms():
    """Get all farms with coordinates"""
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT id, name, latitude, longitude, location 
            FROM farms 
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        """))
        return [dict(row._mapping) for row in result.fetchall()]

def extract_ndvi_for_farms(ndvi_info, farms, tile):
    """Extract NDVI values for farms within the tile coverage"""
    import rasterio
    from pyproj import Transformer
    
    results = []
    
    with rasterio.open(ndvi_info['ndvi_path']) as src:
        ndvi_data = src.read(1)
        transform = src.transform
        bounds = src.bounds
        
        transformer = Transformer.from_crs("EPSG:4326", src.crs, always_xy=True)
        
        for farm in farms:
            try:
                x, y = transformer.transform(farm['longitude'], farm['latitude'])
                
                if bounds.left <= x <= bounds.right and bounds.bottom <= y <= bounds.top:
                    col = int((x - transform.c) / transform.a)
                    row = int((y - transform.f) / transform.e)
                    
                    if 0 <= row < ndvi_data.shape[0] and 0 <= col < ndvi_data.shape[1]:
                        ndvi = ndvi_data[row, col]
                        if not np.isnan(ndvi) and ndvi != -9999:
                            results.append({
                                'farm_id': farm['id'],
                                'farm_name': farm['name'],
                                'ndvi': float(ndvi),
                                'tile': tile
                            })
            except Exception as e:
                pass
    
    return results

def insert_satellite_records(records, date):
    """Insert satellite records into database"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        for r in records:
            extra_metadata = json.dumps({
                'farm_id': r['farm_id'],
                'ndvi_value': r['ndvi'],
                'source': 'sentinel2_real',
                'tile': r['tile'],
                'acquisition_date': date,
                'processed_at': datetime.now().isoformat()
            })
            
            conn.execute(text("""
                INSERT INTO satellite_images (date, region, image_type, file_path, extra_metadata)
                VALUES (:date, :region, 'ndvi', :file_path, CAST(:extra_metadata AS jsonb))
            """), {
                'date': date,
                'region': r['tile'],
                'file_path': f"sentinel2/{r['tile']}/ndvi_{date}.tif",
                'extra_metadata': extra_metadata
            })
        conn.commit()
    
    print(f"   💾 Inserted {len(records)} records")

def main():
    print("=" * 70)
    print("🛰️  DOWNLOAD & PROCESS ALL RWANDA SENTINEL-2 DATA")
    print("=" * 70)
    
    # Get farms
    farms = get_all_farms()
    print(f"\n📊 Total farms: {len(farms)}")
    
    # Get token
    token = get_access_token()
    if not token:
        return
    
    # Search products
    products = search_rwanda_products(token)
    if not products:
        return
    
    # Get best product per tile
    tile_products = get_best_products_per_tile(products)
    print(f"\n📍 Available tiles: {list(tile_products.keys())}")
    
    # Process each tile
    all_results = []
    for tile, product in tile_products.items():
        print(f"\n🛰️  Processing {tile}...")
        
        # Check if we already have this tile's NDVI
        ndvi_path = os.path.join(OUTPUT_DIR, f'ndvi_{tile}.tif')
        if os.path.exists(ndvi_path):
            print(f"   ✓ NDVI already exists")
            import rasterio
            with rasterio.open(ndvi_path) as src:
                ndvi_info = {
                    'ndvi_path': ndvi_path,
                    'crs': src.crs,
                    'transform': src.transform,
                    'bounds': src.bounds
                }
        else:
            # Download
            zip_path = download_product(token, product, OUTPUT_DIR)
            if not zip_path:
                continue
            
            # Calculate NDVI
            ndvi_info = extract_and_calculate_ndvi(zip_path, tile)
            if not ndvi_info:
                continue
        
        # Extract NDVI for farms
        date = product['ContentDate']['Start'][:10]
        results = extract_ndvi_for_farms(ndvi_info, farms, tile)
        print(f"   📊 Farms covered: {len(results)}")
        
        if results:
            insert_satellite_records(results, date)
            all_results.extend(results)
    
    # Final summary
    print("\n" + "=" * 70)
    print("📊 FINAL RESULTS:")
    print(f"   Total farms: {len(farms)}")
    print(f"   Farms with real data: {len(all_results)}")
    
    # Check database
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM satellite_images WHERE extra_metadata->>'source'='sentinel2_real'")).fetchone()[0]
    print(f"   Total real records in DB: {count}")
    print("=" * 70)

if __name__ == "__main__":
    main()
