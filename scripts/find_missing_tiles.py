"""Find Sentinel-2 tiles covering farms without real data."""
import requests
from sqlalchemy import create_engine, text

# Copernicus credentials
USERNAME = "kagaboriziki@gmail.com"
PASSWORD = "Kagaboriziki@183"
TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"


def get_access_token():
    resp = requests.post(TOKEN_URL, data={
        'grant_type': 'password',
        'username': USERNAME,
        'password': PASSWORD,
        'client_id': 'cdse-public'
    })
    return resp.json()['access_token']


def main():
    # Missing farm coordinates
    missing_farms = [
        (14, "Farm M13 - Rusizi", -1.4770, 29.6517),
        (15, "Farm N14 - Huye", -1.5233, 29.6443),
        (16, "Farm O15 - Nyagatare", -1.5093, 29.6556),
        (26, "Farm E5 - Musanze", -1.4646, 29.6118),
        (30, "Farm I9 - Nyagatare", -1.5083, 29.6256),
        (35, "Farm N14 - Karongi", -1.5310, 29.6190),
        (41, "Farm T20 - Nyagatare", -1.5003, 29.5924),
    ]

    print("Missing farms:")
    for fid, name, lat, lon in missing_farms:
        print(f"  ID {fid}: {name} ({lat}, {lon})")

    # Build bounding box around all missing farms
    lats = [f[2] for f in missing_farms]
    lons = [f[3] for f in missing_farms]
    min_lat, max_lat = min(lats) - 0.05, max(lats) + 0.05
    min_lon, max_lon = min(lons) - 0.05, max(lons) + 0.05

    print(f"\nSearching area: lat [{min_lat:.4f}, {max_lat:.4f}], lon [{min_lon:.4f}, {max_lon:.4f}]")

    # Get access token
    token = get_access_token()
    print("✅ Got access token")

    # Search for Sentinel-2 products
    search_url = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
    filter_str = (
        f"Collection/Name eq 'SENTINEL-2' and "
        f"Attributes/OData.CSC.DoubleAttribute/any(att:att/Name eq 'cloudCover' and att/OData.CSC.DoubleAttribute/Value lt 20) and "
        f"OData.CSC.Intersects(area=geography'SRID=4326;POLYGON(({min_lon} {min_lat}, {max_lon} {min_lat}, {max_lon} {max_lat}, {min_lon} {max_lat}, {min_lon} {min_lat}))')"
    )

    params = {
        "$filter": filter_str,
        "$orderby": "ContentDate/Start desc",
        "$top": 20
    }

    resp = requests.get(search_url, params=params, headers={"Authorization": f"Bearer {token}"})
    data = resp.json()

    print(f"\nFound {len(data.get('value', []))} products")

    tiles_found = {}
    for p in data.get("value", []):
        name = p["Name"]
        # Extract tile from name (e.g., S2A_MSIL2A_20250108T081241_N0511_R078_T36MTD_20250108T094623)
        parts = name.split("_")
        for part in parts:
            if len(part) == 6 and part[0] == "T" and part[1:3].isdigit():
                if part not in tiles_found:
                    tiles_found[part] = p
                break

    print(f"\nUnique tiles covering missing farms:")
    for tile, product in tiles_found.items():
        print(f"  {tile}: {product['Name']}")

    # Check which tiles we already have
    engine = create_engine("postgresql://postgres:1234@localhost:5433/crop_risk_db")
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT DISTINCT extra_metadata->>'tile' as tile
            FROM satellite_images
            WHERE extra_metadata->>'source' = 'copernicus_sentinel2'
        """))
        existing_tiles = {row[0] for row in result if row[0]}

    print(f"\nAlready downloaded tiles: {existing_tiles}")
    new_tiles = set(tiles_found.keys()) - existing_tiles
    print(f"New tiles to download: {new_tiles}")


if __name__ == "__main__":
    main()
