"""Check unique farms with real satellite data and clean duplicates"""
from sqlalchemy import create_engine, text

engine = create_engine('postgresql://postgres:1234@localhost:5433/crop_risk_db')
conn = engine.connect()

# Total farms
total_farms = conn.execute(text('SELECT COUNT(*) FROM farms')).fetchone()[0]
print(f"Total farms: {total_farms}")

# Total real satellite records
total_real = conn.execute(text("SELECT COUNT(*) FROM satellite_images WHERE extra_metadata->>'source'='sentinel2_real'")).fetchone()[0]
print(f"Total real satellite records: {total_real}")

# Unique farms with real data
unique_farms = conn.execute(text("""
    SELECT COUNT(DISTINCT (extra_metadata->>'farm_id')::int) 
    FROM satellite_images 
    WHERE extra_metadata->>'source'='sentinel2_real'
""")).fetchone()[0]
print(f"Unique farms with real data: {unique_farms}")

# List farms without real data
farms_without = conn.execute(text("""
    SELECT f.id, f.name, f.location, f.latitude, f.longitude
    FROM farms f
    WHERE f.id NOT IN (
        SELECT DISTINCT (s.extra_metadata->>'farm_id')::int 
        FROM satellite_images s 
        WHERE s.extra_metadata->>'source'='sentinel2_real'
    )
    AND f.latitude IS NOT NULL
""")).fetchall()

print(f"\nFarms without real data: {len(farms_without)}")
for farm in farms_without[:10]:
    print(f"  ID {farm[0]}: {farm[1]} ({farm[3]:.4f}, {farm[4]:.4f})")

# Clean duplicates - keep only most recent per farm
print("\n🧹 Cleaning duplicates...")
conn.execute(text("""
    DELETE FROM satellite_images s1
    WHERE s1.id NOT IN (
        SELECT MAX(s2.id) 
        FROM satellite_images s2 
        WHERE s2.extra_metadata->>'source'='sentinel2_real'
        GROUP BY (s2.extra_metadata->>'farm_id')::int
    )
    AND s1.extra_metadata->>'source'='sentinel2_real'
"""))
conn.commit()

# Final count
final_count = conn.execute(text("SELECT COUNT(*) FROM satellite_images WHERE extra_metadata->>'source'='sentinel2_real'")).fetchone()[0]
print(f"✅ After cleanup: {final_count} records (unique per farm)")

conn.close()
