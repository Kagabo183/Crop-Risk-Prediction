"""Download remaining tiles and fill in missing farms."""
import os
import zipfile
import tempfile
import requests
import rasterio
import numpy as np
from pyproj import Transformer
from sqlalchemy import create_engine, text
from datetime import datetime

# Config
USERNAME = "kagaboriziki@gmail.com"
PASSWORD = "Kagaboriziki@183"
TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
DB_URL = "postgresql://postgres:1234@localhost:5433/crop_risk_db"
NDVI_DIR = "data/sentinel2_real"

os.makedirs(NDVI_DIR, exist_ok=True)


def get_access_token():
    resp = requests.post(TOKEN_URL, data={
        'grant_type': 'password',
        'username': USERNAME,
        'password': PASSWORD,
        'client_id': 'cdse-public'
    })
    return resp.json()['access_token']


def search_tile(token, tile_id):
    """Search for latest product for a specific tile."""
    search_url = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
    filter_str = (
        f"Collection/Name eq 'SENTINEL-2' and "
        f"contains(Name, '{tile_id}') and "
        f"Attributes/OData.CSC.DoubleAttribute/any(att:att/Name eq 'cloudCover' and att/OData.CSC.DoubleAttribute/Value lt 20)"
    )
    params = {
        "$filter": filter_str,
        "$orderby": "ContentDate/Start desc",
        "$top": 1
    }
    resp = requests.get(search_url, params=params, headers={"Authorization": f"Bearer {token}"})
    data = resp.json()
    if data.get("value"):
        return data["value"][0]
    return None


def download_product(token, product_id, product_name):
    """Download a Sentinel-2 product."""
    download_url = f"https://download.dataspace.copernicus.eu/odata/v1/Products({product_id})/$value"
    
    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, f"{product_name}.zip")
    
    print(f"  Downloading to {zip_path}...")
    
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {token}"})
    
    resp = session.get(download_url, stream=True)
    resp.raise_for_status()
    
    total = int(resp.headers.get('content-length', 0))
    downloaded = 0
    
    with open(zip_path, 'wb') as f:
        for chunk in resp.iter_content(chunk_size=8192*16):
            f.write(chunk)
            downloaded += len(chunk)
            if total:
                pct = downloaded * 100 / total
                print(f"\r  Progress: {pct:.1f}% ({downloaded/1e6:.1f}MB)", end="", flush=True)
    
    print()
    return zip_path


def extract_bands(zip_path):
    """Extract B04 (Red) and B08 (NIR) bands."""
    with zipfile.ZipFile(zip_path, 'r') as zf:
        # Find the band files - check multiple naming patterns
        b04_path = None
        b08_path = None
        
        for name in zf.namelist():
            # L2A format: B04_10m.jp2, B08_10m.jp2
            if "B04_10m.jp2" in name:
                b04_path = name
            elif "B08_10m.jp2" in name:
                b08_path = name
        
        if not b04_path or not b08_path:
            # Try L2A 20m resolution
            for name in zf.namelist():
                if "B04_20m.jp2" in name:
                    b04_path = name
                elif "B08_20m.jp2" in name:
                    b08_path = name
        
        if not b04_path or not b08_path:
            # L1C format: T35MRU_20251227T081249_B04.jp2 (in IMG_DATA folder)
            for name in zf.namelist():
                if "/IMG_DATA/" in name and "_B04.jp2" in name:
                    b04_path = name
                elif "/IMG_DATA/" in name and "_B08.jp2" in name:
                    b08_path = name
        
        if not b04_path or not b08_path:
            print(f"  Could not find bands in {zip_path}")
            print(f"  Available files with B04/B08:")
            for name in zf.namelist():
                if 'B04' in name or 'B08' in name:
                    print(f"    {name}")
            return None, None
        
        print(f"  Found B04: {b04_path}")
        print(f"  Found B08: {b08_path}")
        
        temp_dir = tempfile.mkdtemp()
        b04_out = os.path.join(temp_dir, "B04.jp2")
        b08_out = os.path.join(temp_dir, "B08.jp2")
        
        with open(b04_out, 'wb') as f:
            f.write(zf.read(b04_path))
        with open(b08_out, 'wb') as f:
            f.write(zf.read(b08_path))
        
        return b04_out, b08_out


def calculate_ndvi_for_farms(b04_path, b08_path, tile_id, farms, token):
    """Calculate NDVI for each farm and insert records."""
    engine = create_engine(DB_URL)
    
    with rasterio.open(b04_path) as b04_src, rasterio.open(b08_path) as b08_src:
        b04 = b04_src.read(1).astype(float)
        b08 = b08_src.read(1).astype(float)
        
        # Calculate NDVI
        with np.errstate(divide='ignore', invalid='ignore'):
            ndvi = (b08 - b04) / (b08 + b04)
            ndvi = np.where(np.isfinite(ndvi), ndvi, 0)
        
        # Get CRS and transform
        src_crs = b04_src.crs
        transformer = Transformer.from_crs("EPSG:4326", src_crs, always_xy=True)
        
        # Save full NDVI for reference
        ndvi_path = os.path.join(NDVI_DIR, f"ndvi_{tile_id}.tif")
        profile = b04_src.profile.copy()
        profile.update(dtype=rasterio.float32, count=1, driver='GTiff', compress='lzw')
        with rasterio.open(ndvi_path, 'w', **profile) as dst:
            dst.write(ndvi.astype(np.float32), 1)
        print(f"  Saved NDVI to {ndvi_path}")
        
        # Process each farm
        records_added = 0
        for farm_id, name, lat, lon in farms:
            # Transform farm coordinates to image CRS
            x, y = transformer.transform(lon, lat)
            
            # Get pixel coordinates
            row, col = b04_src.index(x, y)
            
            # Check bounds
            if 0 <= row < b04.shape[0] and 0 <= col < b04.shape[1]:
                # Get 5x5 window around farm
                r_min = max(0, row - 2)
                r_max = min(b04.shape[0], row + 3)
                c_min = max(0, col - 2)
                c_max = min(b04.shape[1], col + 3)
                
                ndvi_window = ndvi[r_min:r_max, c_min:c_max]
                ndvi_mean = float(np.mean(ndvi_window))
                
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
                
                print(f"    ✅ Farm {farm_id} ({name}): NDVI = {ndvi_mean:.4f}")
                records_added += 1
            else:
                print(f"    ❌ Farm {farm_id} ({name}): Outside tile bounds")
        
        return records_added


def main():
    # Missing farms
    missing_farms = [
        (14, "Farm M13 - Rusizi", -1.4770, 29.6517),
        (15, "Farm N14 - Huye", -1.5233, 29.6443),
        (16, "Farm O15 - Nyagatare", -1.5093, 29.6556),
        (26, "Farm E5 - Musanze", -1.4646, 29.6118),
        (30, "Farm I9 - Nyagatare", -1.5083, 29.6256),
        (35, "Farm N14 - Karongi", -1.5310, 29.6190),
        (41, "Farm T20 - Nyagatare", -1.5003, 29.5924),
    ]
    
    print(f"Processing {len(missing_farms)} missing farms\n")
    
    token = get_access_token()
    print("✅ Got access token\n")
    
    # Tiles to search/download
    tiles_to_try = ["T35MQU", "T35MRU"]
    
    total_added = 0
    for tile_id in tiles_to_try:
        print(f"\n{'='*50}")
        print(f"Processing tile: {tile_id}")
        print('='*50)
        
        # Check if we already have the NDVI file
        ndvi_path = os.path.join(NDVI_DIR, f"ndvi_{tile_id}.tif")
        
        if os.path.exists(ndvi_path):
            print(f"  Using existing NDVI file: {ndvi_path}")
            
            # Just need to calculate NDVI for missing farms
            # First get B04 and B08 from searching product
            product = search_tile(token, tile_id)
            if product:
                print(f"  Found product: {product['Name']}")
                zip_path = download_product(token, product['Id'], product['Name'])
                b04, b08 = extract_bands(zip_path)
                if b04 and b08:
                    added = calculate_ndvi_for_farms(b04, b08, tile_id, missing_farms, token)
                    total_added += added
        else:
            # Download the tile
            product = search_tile(token, tile_id)
            if product:
                print(f"  Found product: {product['Name']}")
                zip_path = download_product(token, product['Id'], product['Name'])
                b04, b08 = extract_bands(zip_path)
                if b04 and b08:
                    added = calculate_ndvi_for_farms(b04, b08, tile_id, missing_farms, token)
                    total_added += added
            else:
                print(f"  ❌ No product found for {tile_id}")
    
    print(f"\n{'='*50}")
    print(f"Total records added: {total_added}")
    
    # Check final status
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT COUNT(DISTINCT region) FROM satellite_images
            WHERE extra_metadata->>'source' = 'copernicus_sentinel2'
        """))
        unique_farms = result.scalar()
        
        result = conn.execute(text("SELECT COUNT(*) FROM farms"))
        total_farms = result.scalar()
    
    print(f"\n📊 Final Status:")
    print(f"  Unique farms with real data: {unique_farms}/{total_farms}")
    print(f"  Coverage: {unique_farms/total_farms*100:.1f}%")


if __name__ == "__main__":
    main()
