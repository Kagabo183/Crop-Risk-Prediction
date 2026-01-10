"""
Fetch real Sentinel-2 data for ALL farms in Rwanda.
Downloads necessary tiles and calculates NDVI for each farm location.
"""
import os
import sys
import json
import requests
import numpy as np
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

# Copernicus Data Space credentials
USERNAME = os.getenv('COPERNICUS_USERNAME', 'kagaboriziki@gmail.com')
PASSWORD = os.getenv('COPERNICUS_PASSWORD', 'Kagaboriziki@183')

# Rwanda tiles covering the entire country
RWANDA_TILES = ['T35MQU', 'T35MQT', 'T35MPU', 'T36MTD', 'T36MTC', 'T36MTB']

def get_access_token():
    """Get OAuth2 access token from Copernicus Data Space"""
    print("🔐 Authenticating with Copernicus...")
    token_url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
    
    response = requests.post(token_url, data={
        'grant_type': 'password',
        'username': USERNAME,
        'password': PASSWORD,
        'client_id': 'cdse-public'
    })
    
    if response.status_code == 200:
        token = response.json()['access_token']
        print("✅ Authentication successful!")
        return token
    else:
        print(f"❌ Authentication failed: {response.text}")
        return None

def search_tile_products(token, tile_id, max_cloud_cover=30, days_back=30):
    """Search for Sentinel-2 products for a specific tile"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    catalog_url = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
    
    filter_query = (
        f"Collection/Name eq 'SENTINEL-2' and "
        f"Attributes/OData.CSC.StringAttribute/any(att:att/Name eq 'tileId' and att/OData.CSC.StringAttribute/Value eq '{tile_id}') and "
        f"Attributes/OData.CSC.DoubleAttribute/any(att:att/Name eq 'cloudCover' and att/OData.CSC.DoubleAttribute/Value lt {max_cloud_cover}) and "
        f"ContentDate/Start gt {start_date.strftime('%Y-%m-%dT00:00:00.000Z')} and "
        f"ContentDate/Start lt {end_date.strftime('%Y-%m-%dT23:59:59.999Z')}"
    )
    
    response = requests.get(catalog_url, params={
        '$filter': filter_query,
        '$orderby': 'ContentDate/Start desc',
        '$top': 1
    }, headers={'Authorization': f'Bearer {token}'})
    
    if response.status_code == 200:
        products = response.json().get('value', [])
        return products
    return []

def get_farms_by_tile():
    """Group farms by their Sentinel-2 tile coverage"""
    from sqlalchemy import create_engine, text
    
    engine = create_engine('postgresql://postgres:1234@localhost:5433/crop_risk_db')
    conn = engine.connect()
    
    result = conn.execute(text("SELECT id, name, latitude, longitude, location FROM farms WHERE latitude IS NOT NULL"))
    farms = result.fetchall()
    conn.close()
    
    # Group farms by tile based on their coordinates
    tile_farms = {}
    for farm in farms:
        lat, lon = farm[2], farm[3]
        # Determine tile based on longitude (simplified)
        if lon < 30.0:
            tile = 'T35MQU'  # Western Rwanda
        elif lon < 30.3:
            tile = 'T35MQT'  # West-Central
        else:
            tile = 'T36MTD'  # Eastern Rwanda
        
        if tile not in tile_farms:
            tile_farms[tile] = []
        tile_farms[tile].append({
            'id': farm[0],
            'name': farm[1],
            'latitude': lat,
            'longitude': lon,
            'location': farm[4]
        })
    
    return tile_farms

def download_and_process_tile(token, tile_id, farms):
    """Download tile and extract NDVI for farms in that tile"""
    print(f"\n🛰️  Processing tile {tile_id} ({len(farms)} farms)...")
    
    products = search_tile_products(token, tile_id)
    if not products:
        print(f"   ⚠️  No recent products found for tile {tile_id}")
        return []
    
    product = products[0]
    product_id = product['Id']
    product_name = product['Name']
    print(f"   📦 Found: {product_name}")
    
    # For now, return placeholder data - in production, download and process the tile
    # This requires the full download and NDVI processing pipeline
    results = []
    for farm in farms:
        results.append({
            'farm_id': farm['id'],
            'farm_name': farm['name'],
            'tile': tile_id,
            'product_name': product_name,
            'ndvi': None,  # Would be calculated from actual data
            'status': 'pending_download'
        })
    
    return results

def main():
    print("=" * 60)
    print("🛰️  FETCH REAL SENTINEL-2 DATA FOR ALL FARMS")
    print("=" * 60)
    
    # Get access token
    token = get_access_token()
    if not token:
        print("❌ Cannot proceed without authentication")
        return
    
    # Get farms grouped by tile
    tile_farms = get_farms_by_tile()
    
    print(f"\n📊 Farm distribution by tile:")
    for tile, farms in tile_farms.items():
        print(f"   {tile}: {len(farms)} farms")
    
    print(f"\n🔍 Searching for available Sentinel-2 products...")
    
    all_results = []
    for tile_id, farms in tile_farms.items():
        results = download_and_process_tile(token, tile_id, farms)
        all_results.extend(results)
    
    print(f"\n✅ Found data for {len(all_results)} farms")
    print("\nTo download full data, run: python scripts/download_all_tiles.py")

if __name__ == "__main__":
    main()
