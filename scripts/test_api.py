"""Test the farm-satellite API endpoint"""
import requests

# Try port 8001 first, then 8000
for port in [8001, 8000]:
    try:
        r = requests.get(f'http://localhost:{port}/api/v1/farm-satellite/', timeout=3)
        data = r.json()
        print(f"Connected to port {port}")
        break
    except:
        continue
else:
    print("Could not connect to API")
    exit(1)

real = [f for f in data if f.get('data_source') == 'real']
simulated = [f for f in data if f.get('data_source') != 'real']

print(f"Total farms: {len(data)}")
print(f"Real Sentinel-2: {len(real)}")
print(f"Simulated: {len(simulated)}")
print()

if real:
    print("Real Satellite Data Farms:")
    print("-" * 60)
    for f in real:
        print(f"  {f['name']}: NDVI={f['ndvi']}, Status={f['ndvi_status']}, Tile={f.get('tile', 'N/A')}")
else:
    print("No real satellite data found")
