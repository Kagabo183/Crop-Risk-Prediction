"""
Remove all simulated satellite data and keep only real Sentinel-2 data.
Then fetch real data for all farms.
"""
from sqlalchemy import create_engine, text

engine = create_engine('postgresql://postgres:1234@localhost:5433/crop_risk_db')
conn = engine.connect()

# Count current data
farms = conn.execute(text('SELECT COUNT(*) FROM farms')).fetchone()[0]
total_sat = conn.execute(text('SELECT COUNT(*) FROM satellite_images')).fetchone()[0]
real_sat = conn.execute(text("SELECT COUNT(*) FROM satellite_images WHERE extra_metadata->>'source'='sentinel2_real'")).fetchone()[0]
simulated = total_sat - real_sat

print(f"📊 Current Status:")
print(f"   Farms: {farms}")
print(f"   Total satellite images: {total_sat}")
print(f"   Real Sentinel-2: {real_sat}")
print(f"   Simulated (to delete): {simulated}")
print()

# Delete all simulated data
if simulated > 0:
    print(f"🗑️  Deleting {simulated} simulated satellite images...")
    conn.execute(text("DELETE FROM satellite_images WHERE extra_metadata->>'source' IS NULL OR extra_metadata->>'source' != 'sentinel2_real'"))
    conn.commit()
    print("✅ Deleted all simulated data!")
else:
    print("✅ No simulated data to delete")

# Verify
remaining = conn.execute(text('SELECT COUNT(*) FROM satellite_images')).fetchone()[0]
print(f"\n📊 After cleanup:")
print(f"   Remaining satellite images: {remaining} (all real)")

conn.close()
