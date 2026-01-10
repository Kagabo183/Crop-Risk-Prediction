"""Check NDVI distribution in the database."""
from sqlalchemy import create_engine, text
import json

engine = create_engine('postgresql://postgres:1234@localhost:5433/crop_risk_db')

with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT region, extra_metadata FROM satellite_images
        WHERE extra_metadata->>'source' = 'copernicus_sentinel2'
        ORDER BY (extra_metadata->>'ndvi_mean')::float
    """))
    
    zero_count = 0
    good_count = 0
    zero_farms = []
    good_farms = []
    
    for row in result:
        meta = row[1] if isinstance(row[1], dict) else json.loads(row[1])
        ndvi = meta.get('ndvi_mean', 0)
        farm_id = meta.get('farm_id')
        tile = meta.get('tile', 'unknown')
        
        if ndvi == 0:
            zero_count += 1
            zero_farms.append((farm_id, ndvi, tile))
        else:
            good_count += 1
            good_farms.append((farm_id, ndvi, tile))
    
    print(f'Farms with NDVI > 0: {good_count}')
    print(f'Farms with NDVI = 0: {zero_count}')
    
    if zero_farms:
        print(f'\nFarms with zero NDVI (need better tiles):')
        for farm_id, ndvi, tile in zero_farms[:10]:
            print(f'  Farm {farm_id}: NDVI={ndvi:.4f} from tile {tile}')
    
    print(f'\nSample of good NDVI values:')
    for farm_id, ndvi, tile in good_farms[-5:]:
        print(f'  Farm {farm_id}: NDVI={ndvi:.4f} from tile {tile}')
