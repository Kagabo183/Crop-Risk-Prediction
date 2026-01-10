"""
Search Sentinel-2 products by bounding box for Rwanda
"""
import requests
from datetime import datetime, timedelta

# Auth
r = requests.post('https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token',
    data={'grant_type': 'password', 'username': 'kagaboriziki@gmail.com', 'password': 'Kagaboriziki@183', 'client_id': 'cdse-public'})
token = r.json()['access_token']
print('✅ Authenticated')

# Search by bounding box (Rwanda)
end = datetime.now()
start = end - timedelta(days=30)

url = 'https://catalogue.dataspace.copernicus.eu/odata/v1/Products'
polygon = "POLYGON((28.8 -2.9, 30.9 -2.9, 30.9 -1.0, 28.8 -1.0, 28.8 -2.9))"
filter_str = f"Collection/Name eq 'SENTINEL-2' and OData.CSC.Intersects(area=geography'SRID=4326;{polygon}') and ContentDate/Start gt {start.strftime('%Y-%m-%dT00:00:00.000Z')}"

r = requests.get(url, params={'$filter': filter_str, '$top': 20, '$orderby': 'ContentDate/Start desc'}, headers={'Authorization': f'Bearer {token}'})
print(f'Status: {r.status_code}')

if r.status_code == 200:
    data = r.json()
    products = data.get('value', [])
    print(f"Products found: {len(products)}")
    for p in products[:10]:
        print(f"  {p['Name'][:70]}...")
        print(f"    Date: {p['ContentDate']['Start'][:10]}, Size: {p.get('ContentLength', 0)/1024/1024:.0f} MB")
else:
    print(f"Error: {r.text[:500]}")
