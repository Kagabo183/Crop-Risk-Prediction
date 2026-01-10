"""Add province field to farms and update with Rwanda province data"""
from sqlalchemy import create_engine, text

# Rwanda districts to provinces mapping
DISTRICT_TO_PROVINCE = {
    # Kigali City (Umujyi wa Kigali)
    'Gasabo': 'Kigali',
    'Kicukiro': 'Kigali', 
    'Nyarugenge': 'Kigali',
    
    # Northern Province (Amajyaruguru)
    'Burera': 'Northern',
    'Gakenke': 'Northern',
    'Gicumbi': 'Northern',
    'Musanze': 'Northern',
    'Rulindo': 'Northern',
    
    # Southern Province (Amajyepfo)
    'Gisagara': 'Southern',
    'Huye': 'Southern',
    'Kamonyi': 'Southern',
    'Muhanga': 'Southern',
    'Nyamagabe': 'Southern',
    'Nyanza': 'Southern',
    'Nyaruguru': 'Southern',
    'Ruhango': 'Southern',
    
    # Eastern Province (Iburasirazuba)
    'Bugesera': 'Eastern',
    'Gatsibo': 'Eastern',
    'Kayonza': 'Eastern',
    'Kirehe': 'Eastern',
    'Ngoma': 'Eastern',
    'Nyagatare': 'Eastern',
    'Rwamagana': 'Eastern',
    
    # Western Province (Iburengerazuba)
    'Karongi': 'Western',
    'Ngororero': 'Western',
    'Nyabihu': 'Western',
    'Nyamasheke': 'Western',
    'Rubavu': 'Western',
    'Rusizi': 'Western',
    'Rutsiro': 'Western',
}

engine = create_engine('postgresql://postgres:1234@localhost:5433/crop_risk_db')

with engine.connect() as conn:
    # Add province column if not exists
    try:
        conn.execute(text("ALTER TABLE farms ADD COLUMN province VARCHAR(50)"))
        conn.commit()
        print("✅ Added province column to farms table")
    except Exception as e:
        conn.rollback() # <--- Added rollback here
        if 'already exists' in str(e):
            print("ℹ️  Province column already exists")
        else:
            print(f"Note: {e}")
    
    # Update provinces based on district in location
    updated = 0
    for district, province in DISTRICT_TO_PROVINCE.items():
        result = conn.execute(
            text("UPDATE farms SET province = :province WHERE location LIKE :pattern AND (province IS NULL OR province = '')"),
            {'province': province, 'pattern': f'%{district}%'}
        )
        updated += result.rowcount
    
    conn.commit()
    print(f"✅ Updated {updated} farms with province data")
    
    # Show summary
    result = conn.execute(text("""
        SELECT province, COUNT(*) as farm_count 
        FROM farms 
        GROUP BY province 
        ORDER BY province
    """))
    print("\n=== Farms by Province ===")
    for row in result:
        print(f"  {row[0] or 'Unknown'}: {row[1]} farms")
    
    # Show districts
    result = conn.execute(text("""
        SELECT province, location, COUNT(*) as farm_count 
        FROM farms 
        GROUP BY province, location 
        ORDER BY province, location
    """))
    print("\n=== Farms by Province > District ===")
    for row in result:
        print(f"  {row[0] or 'Unknown'} > {row[1]}: {row[2]} farms")
