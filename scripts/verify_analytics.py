"""Verify pipeline analytics"""
from app.services.pipeline_service import get_pipeline_service

p = get_pipeline_service()

print("=== Province Analytics ===")
provs = p.get_province_analytics()
for pr in provs:
    print(f"  {pr['province']}: {pr['farm_count']} farms, NDVI={pr['avg_ndvi']:.4f}, Risk={pr['risk_level']}")

print("\n=== District Analytics ===")
dists = p.get_district_analytics()
for d in dists:
    print(f"  {d['district'].split(',')[0]}: {d['farm_count']} farms, NDVI={d['avg_ndvi']:.4f}, Risk={d['risk_level']}")

print("\n=== Summary ===")
summary = p.get_prediction_summary()
print(f"  Total Farms: {summary['total_farms']}")
print(f"  Total Provinces: {summary['total_provinces']}")
print(f"  Total Districts: {summary['total_districts']}")
print(f"  Average NDVI: {summary['average_ndvi']:.4f}")
print(f"  Overall Health: {summary['overall_health']}")
print(f"  Overall Risk: {summary['overall_risk']}")
