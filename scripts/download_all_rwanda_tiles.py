"""
Download multiple Sentinel-2 tiles to cover all of Rwanda
"""
import os
import sys
import requests
from datetime import datetime, timedelta
from pathlib import Path

# Copernicus API endpoints
CDSE_TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
CDSE_CATALOG_URL = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"

# Rwanda is covered by multiple Sentinel-2 tiles
# Main tiles for Rwanda: T35MQU, T35MQT, T35MPU, T36MTB, T36MTD
RWANDA_TILES = ["35MQU", "35MQT", "35MPU", "36MTB", "36MTD"]

def get_access_token(username: str, password: str) -> str:
    """Get access token from Copernicus Data Space"""
    data = {
        "client_id": "cdse-public",
        "username": username,
        "password": password,
        "grant_type": "password",
    }
    response = requests.post(CDSE_TOKEN_URL, data=data)
    response.raise_for_status()
    return response.json()["access_token"]


def search_tile(tile_id: str, start_date: str, end_date: str, cloud_max: int = 30):
    """Search for a specific Sentinel-2 tile"""
    # Build filter for specific tile
    tile_filter = f"contains(Name,'{tile_id}')"
    date_filter = f"ContentDate/Start gt {start_date}T00:00:00.000Z and ContentDate/Start lt {end_date}T23:59:59.999Z"
    collection_filter = "Collection/Name eq 'SENTINEL-2'"
    cloud_filter = f"Attributes/OData.CSC.DoubleAttribute/any(att:att/Name eq 'cloudCover' and att/OData.CSC.DoubleAttribute/Value lt {cloud_max})"
    
    full_filter = f"{tile_filter} and {date_filter} and {collection_filter} and {cloud_filter}"
    
    params = {
        "$filter": full_filter,
        "$orderby": "ContentDate/Start desc",
        "$top": 1,
        "$expand": "Attributes"
    }
    
    response = requests.get(CDSE_CATALOG_URL, params=params)
    response.raise_for_status()
    
    return response.json().get("value", [])


def download_product(product_id: str, access_token: str, output_dir: Path) -> Path:
    """Download a Sentinel-2 product"""
    download_url = f"https://zipper.dataspace.copernicus.eu/odata/v1/Products({product_id})/$value"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = requests.get(download_url, headers=headers, stream=True)
    response.raise_for_status()
    
    output_file = output_dir / f"{product_id}.zip"
    total_size = int(response.headers.get('content-length', 0))
    
    downloaded = 0
    with open(output_file, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            downloaded += len(chunk)
            if total_size:
                percent = (downloaded / total_size) * 100
                print(f"\r   Progress: {percent:.1f}% ({downloaded/(1024*1024):.1f} MB)", end="")
    print()
    
    return output_file


def main():
    print("=" * 60)
    print("🛰️  DOWNLOAD ALL RWANDA SENTINEL-2 TILES")
    print("=" * 60)
    
    username = os.environ.get("COPERNICUS_USERNAME")
    password = os.environ.get("COPERNICUS_PASSWORD")
    
    if not username or not password:
        print("❌ Set COPERNICUS_USERNAME and COPERNICUS_PASSWORD environment variables")
        return
    
    print("\n🔐 Authenticating...")
    access_token = get_access_token(username, password)
    print("✅ Authenticated!")
    
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
    
    output_dir = Path(__file__).parent.parent / "data" / "sentinel2_real"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n📅 Searching for tiles from {start_date} to {end_date}")
    print(f"📂 Output directory: {output_dir}")
    
    downloaded = []
    for tile in RWANDA_TILES:
        print(f"\n🔍 Searching for tile T{tile}...")
        products = search_tile(tile, start_date, end_date, cloud_max=30)
        
        if products:
            product = products[0]
            name = product.get("Name", "Unknown")
            cloud = None
            for attr in product.get("Attributes", []):
                if attr.get("Name") == "cloudCover":
                    cloud = attr.get("Value")
            print(f"   Found: {name} (Cloud: {cloud:.1f}%)")
            
            # Check if already downloaded
            existing = list(output_dir.glob(f"*{tile}*"))
            if existing:
                print(f"   ⏭️  Already downloaded, skipping")
                continue
            
            print(f"   📥 Downloading...")
            try:
                output_file = download_product(product["Id"], access_token, output_dir)
                downloaded.append(tile)
                print(f"   ✅ Saved to: {output_file.name}")
            except Exception as e:
                print(f"   ❌ Failed: {e}")
        else:
            print(f"   ⚠️  No recent imagery found for this tile")
    
    print("\n" + "=" * 60)
    print(f"✅ Downloaded {len(downloaded)} new tiles: {downloaded}")
    print("=" * 60)


if __name__ == "__main__":
    main()
