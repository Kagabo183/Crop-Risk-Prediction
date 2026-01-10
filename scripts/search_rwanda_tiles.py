"""
Download ALL available Sentinel-2 tiles for Rwanda with relaxed cloud cover.
"""
import os
import sys
import json
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

USERNAME = os.getenv('COPERNICUS_USERNAME', 'kagaboriziki@gmail.com')
PASSWORD = os.getenv('COPERNICUS_PASSWORD', 'Kagaboriziki@183')

# All Rwanda tiles
RWANDA_TILES = ['T35MPU', 'T35MQU', 'T35MQT', 'T36MTB', 'T36MTC', 'T36MTD']

def get_access_token():
    print("🔐 Authenticating...")
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

def search_products(token, tile_id, max_cloud=80, days_back=90):
    """Search with relaxed parameters"""
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
        params={'$filter': filter_query, '$orderby': 'Attributes/OData.CSC.DoubleAttribute/Value asc', '$top': 5},
        headers={'Authorization': f'Bearer {token}'}
    )
    
    if response.status_code == 200:
        return response.json().get('value', [])
    return []

def main():
    print("=" * 70)
    print("🛰️  SEARCH ALL RWANDA SENTINEL-2 TILES")
    print("=" * 70)
    
    token = get_access_token()
    if not token:
        return
    
    print("\nSearching with relaxed parameters (80% cloud, 90 days)...\n")
    
    found_tiles = {}
    for tile in RWANDA_TILES:
        print(f"🔍 {tile}...", end=" ")
        products = search_products(token, tile)
        if products:
            best = products[0]
            # Extract cloud cover
            cloud_cover = None
            for attr in best.get('Attributes', []):
                if attr.get('Name') == 'cloudCover':
                    cloud_cover = attr.get('Value')
                    break
            
            print(f"✅ Found {len(products)} products")
            print(f"   Best: {best['Name'][:50]}...")
            print(f"   Cloud: {cloud_cover}%, Date: {best['ContentDate']['Start'][:10]}")
            found_tiles[tile] = {
                'id': best['Id'],
                'name': best['Name'],
                'cloud_cover': cloud_cover,
                'date': best['ContentDate']['Start'][:10]
            }
        else:
            print("❌ No products")
    
    print("\n" + "=" * 70)
    print("📊 SUMMARY:")
    print(f"   Tiles found: {len(found_tiles)}/{len(RWANDA_TILES)}")
    for tile, info in found_tiles.items():
        print(f"   {tile}: Cloud {info['cloud_cover']}%, Date {info['date']}")
    
    # Save for later download
    with open('data/rwanda_tiles_available.json', 'w') as f:
        json.dump(found_tiles, f, indent=2)
    print("\n✅ Saved to data/rwanda_tiles_available.json")

if __name__ == "__main__":
    main()
