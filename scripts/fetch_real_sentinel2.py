"""
Real Sentinel-2 Data Fetcher
Fetches actual satellite imagery from Copernicus Data Space Ecosystem

Prerequisites:
1. Create a free account at: https://dataspace.copernicus.eu/
2. Set environment variables:
   - COPERNICUS_USERNAME=your_email
   - COPERNICUS_PASSWORD=your_password

Or use the Sentinel Hub API (has free tier):
1. Register at: https://www.sentinel-hub.com/
2. Get API credentials
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    import rasterio
    from rasterio.transform import from_bounds
    import numpy as np
    HAS_RASTERIO = True
except ImportError:
    HAS_RASTERIO = False
    print("Warning: rasterio not installed. Run: pip install rasterio")

# Rwanda bounding box
RWANDA_BBOX = {
    "min_lon": 28.8,
    "min_lat": -2.9,
    "max_lon": 30.9,
    "max_lat": -1.0
}

# Copernicus Data Space API endpoints
CDSE_TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
CDSE_CATALOG_URL = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"


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


def search_sentinel2_products(
    bbox: dict,
    start_date: str,
    end_date: str,
    cloud_cover_max: int = 30,
    limit: int = 10
) -> list:
    """
    Search for Sentinel-2 products in Copernicus Data Space
    
    Args:
        bbox: Bounding box with min_lon, min_lat, max_lon, max_lat
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        cloud_cover_max: Maximum cloud cover percentage
        limit: Maximum number of results
    
    Returns:
        List of product metadata
    """
    # Build OData filter
    geometry_filter = f"OData.CSC.Intersects(area=geography'SRID=4326;POLYGON(({bbox['min_lon']} {bbox['min_lat']},{bbox['max_lon']} {bbox['min_lat']},{bbox['max_lon']} {bbox['max_lat']},{bbox['min_lon']} {bbox['max_lat']},{bbox['min_lon']} {bbox['min_lat']}))')"
    
    date_filter = f"ContentDate/Start gt {start_date}T00:00:00.000Z and ContentDate/Start lt {end_date}T23:59:59.999Z"
    
    collection_filter = "Collection/Name eq 'SENTINEL-2'"
    
    cloud_filter = f"Attributes/OData.CSC.DoubleAttribute/any(att:att/Name eq 'cloudCover' and att/OData.CSC.DoubleAttribute/Value lt {cloud_cover_max})"
    
    full_filter = f"{geometry_filter} and {date_filter} and {collection_filter} and {cloud_filter}"
    
    params = {
        "$filter": full_filter,
        "$orderby": "ContentDate/Start desc",
        "$top": limit,
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
    
    with open(output_file, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    return output_file


def fetch_real_sentinel2_for_farms():
    """
    Fetch real Sentinel-2 data for farms in the database
    """
    # Check for credentials
    username = os.environ.get("COPERNICUS_USERNAME")
    password = os.environ.get("COPERNICUS_PASSWORD")
    
    if not username or not password:
        print("=" * 60)
        print("⚠️  COPERNICUS CREDENTIALS NOT SET")
        print("=" * 60)
        print()
        print("To fetch real Sentinel-2 data, you need to:")
        print()
        print("1. Create a FREE account at:")
        print("   https://dataspace.copernicus.eu/")
        print()
        print("2. Set environment variables:")
        print("   Windows PowerShell:")
        print('   $env:COPERNICUS_USERNAME="your_email@example.com"')
        print('   $env:COPERNICUS_PASSWORD="your_password"')
        print()
        print("   Or add to .env file:")
        print("   COPERNICUS_USERNAME=your_email@example.com")
        print("   COPERNICUS_PASSWORD=your_password")
        print()
        print("3. Run this script again")
        print("=" * 60)
        
        # Show what data is available (no auth needed for search)
        print("\n📡 Searching for available Sentinel-2 data over Rwanda...")
        
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        try:
            products = search_sentinel2_products(
                RWANDA_BBOX,
                start_date,
                end_date,
                cloud_cover_max=30,
                limit=5
            )
            
            if products:
                print(f"\n✅ Found {len(products)} recent Sentinel-2 images:")
                for p in products:
                    name = p.get("Name", "Unknown")
                    date = p.get("ContentDate", {}).get("Start", "")[:10]
                    cloud = None
                    for attr in p.get("Attributes", []):
                        if attr.get("Name") == "cloudCover":
                            cloud = attr.get("Value")
                    print(f"   📷 {name}")
                    print(f"      Date: {date}, Cloud: {cloud:.1f}%")
            else:
                print("No products found for the specified criteria")
        except Exception as e:
            print(f"Search error: {e}")
        
        return
    
    # With credentials, proceed to download
    print("🔐 Authenticating with Copernicus Data Space...")
    try:
        access_token = get_access_token(username, password)
        print("✅ Authentication successful!")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return
    
    # Search for recent imagery
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
    
    print(f"\n🛰️  Searching for Sentinel-2 imagery from {start_date} to {end_date}...")
    
    products = search_sentinel2_products(
        RWANDA_BBOX,
        start_date,
        end_date,
        cloud_cover_max=30,
        limit=5
    )
    
    if not products:
        print("❌ No suitable imagery found. Try expanding date range or cloud cover threshold.")
        return
    
    print(f"✅ Found {len(products)} products:")
    for p in products:
        name = p.get("Name", "Unknown")
        cloud = None
        for attr in p.get("Attributes", []):
            if attr.get("Name") == "cloudCover":
                cloud = attr.get("Value")
        print(f"   📷 {name} (Cloud: {cloud:.1f}%)")
    
    # Create output directory
    output_dir = Path(os.path.dirname(__file__)) / ".." / "data" / "sentinel2_real"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Download first product (best cloud cover)
    product = products[0]
    print(f"\n📥 Downloading: {product['Name']}...")
    print("   This may take several minutes (files are ~700MB-1GB)...")
    
    try:
        output_file = download_product(product["Id"], access_token, output_dir)
        print(f"✅ Downloaded to: {output_file}")
        print("\n" + "=" * 60)
        print("📦 NEXT STEPS:")
        print("=" * 60)
        print("1. Extract the ZIP file")
        print("2. Find B04 (Red) and B08 (NIR) bands in GRANULE/*/IMG_DATA/")
        print("3. Calculate NDVI = (B08 - B04) / (B08 + B04)")
        print("4. Use geo-coordinates from the .jp2 files to locate farms")
        print("=" * 60)
    except Exception as e:
        print(f"❌ Download failed: {e}")


def calculate_ndvi_from_bands(red_band: np.ndarray, nir_band: np.ndarray) -> np.ndarray:
    """
    Calculate NDVI from Red and NIR bands
    
    NDVI = (NIR - Red) / (NIR + Red)
    
    For Sentinel-2:
    - Red = Band 4 (B04)
    - NIR = Band 8 (B08)
    """
    # Avoid division by zero
    denominator = nir_band.astype(float) + red_band.astype(float)
    ndvi = np.where(
        denominator > 0,
        (nir_band.astype(float) - red_band.astype(float)) / denominator,
        0
    )
    return ndvi.astype(np.float32)


if __name__ == "__main__":
    print("=" * 60)
    print("🛰️  REAL SENTINEL-2 DATA FETCHER")
    print("=" * 60)
    print()
    fetch_real_sentinel2_for_farms()
