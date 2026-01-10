"""Check database structure for pipeline planning"""
from sqlalchemy import create_engine, text

engine = create_engine('postgresql://postgres:1234@localhost:5433/crop_risk_db')

with engine.connect() as conn:
    # Check farms table structure
    result = conn.execute(text("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'farms' 
        ORDER BY ordinal_position
    """))
    print('=== Farms Table Schema ===')
    for row in result:
        print(f'  {row[0]}: {row[1]}')
    
    # Check unique locations (districts)
    result = conn.execute(text('SELECT DISTINCT location FROM farms ORDER BY location'))
    print('\n=== Unique Locations (Districts) ===')
    locations = [row[0] for row in result]
    for loc in locations:
        print(f'  {loc}')
    print(f'\nTotal unique locations: {len(locations)}')
    
    # Sample farms
    result = conn.execute(text('SELECT id, name, location, latitude, longitude FROM farms LIMIT 5'))
    print('\n=== Sample Farms ===')
    for row in result:
        print(f'  ID {row[0]}: {row[1]} @ {row[2]} ({row[3]}, {row[4]})')
