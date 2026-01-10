"""Check actual farm coverage with real satellite data."""
from sqlalchemy import create_engine, text

engine = create_engine('postgresql://postgres:1234@localhost:5433/crop_risk_db')

with engine.connect() as conn:
    # Total farms
    result = conn.execute(text('SELECT COUNT(*) FROM farms'))
    total_farms = result.scalar()
    
    # Total real records
    result = conn.execute(text("""
        SELECT COUNT(*) FROM satellite_images
        WHERE extra_metadata->>'source' = 'copernicus_sentinel2'
    """))
    total_records = result.scalar()
    
    # Unique farms with real data
    result = conn.execute(text("""
        SELECT COUNT(DISTINCT (extra_metadata->>'farm_id')::int) FROM satellite_images
        WHERE extra_metadata->>'source' = 'copernicus_sentinel2'
    """))
    unique_farms = result.scalar()
    
    print(f'Total farms: {total_farms}')
    print(f'Total real satellite records: {total_records}')
    print(f'Unique farms with real data: {unique_farms}')
    print(f'Coverage: {unique_farms}/{total_farms} ({unique_farms/total_farms*100:.1f}%)')
    
    # Check which farms are missing
    result = conn.execute(text("""
        SELECT f.id, f.name, f.location 
        FROM farms f
        WHERE NOT EXISTS (
            SELECT 1 FROM satellite_images s 
            WHERE s.extra_metadata->>'source' = 'copernicus_sentinel2'
            AND (s.extra_metadata->>'farm_id')::int = f.id
        )
        ORDER BY f.id
    """))
    missing = result.fetchall()
    
    if missing:
        print(f'\nFarms without real data: {len(missing)}')
        for row in missing:
            print(f'  ID {row[0]}: {row[1]} ({row[2]})')
    else:
        print('\n✅ ALL FARMS HAVE REAL SATELLITE DATA!')
