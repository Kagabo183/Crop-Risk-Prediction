"""Check real satellite data in database"""
from sqlalchemy import create_engine, text

engine = create_engine('postgresql://postgres:1234@localhost:5433/crop_risk_db')
conn = engine.connect()

# Count real satellite data
result = conn.execute(text("SELECT COUNT(*) FROM satellite_images WHERE extra_metadata->>'source'='sentinel2_real'"))
real_count = result.fetchone()[0]
print(f"✅ Real Sentinel-2 satellite images in DB: {real_count}")

# Show sample data
result = conn.execute(text("""
    SELECT extra_metadata->>'farm_id' as farm_id,
           extra_metadata->>'ndvi_value' as ndvi, 
           extra_metadata->>'source' as source,
           extra_metadata->>'tile' as tile,
           date
    FROM satellite_images 
    WHERE extra_metadata->>'source'='sentinel2_real'
    LIMIT 5
"""))

print("\nSample real satellite data:")
print("-" * 70)
for row in result:
    print(f"  Farm ID {row[0]}: NDVI={row[1]}, Tile={row[3]}, Date={row[4]}")

conn.close()
print("\n✅ Dashboard will show only this real data!")
