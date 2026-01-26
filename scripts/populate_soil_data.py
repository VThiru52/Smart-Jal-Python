"""
Script to populate soil_types table with representative soil data for Krishna District
"""
from app.core.supabase import get_supabase_admin

# Representative soil types for Krishna District, Andhra Pradesh
SOIL_SAMPLES = [
    {
        "soil_code": "ALV-01",
        "soil_name": "Alluvial Soils - Fine Loamy",
        "texture": "Loamy",
        "drainage_class": "Well Drained",
        "area_ha": 3178.88
    },
    {
        "soil_code": "ALV-02",
        "soil_name": "Alluvial Soils - Clayey",
        "texture": "Clayey",
        "drainage_class": "Moderately Drained",
        "area_ha": 1537.82
    },
    {
        "soil_code": "BLK-01",
        "soil_name": "Black Cotton Soils",
        "texture": "Clay",
        "drainage_class": "Poorly Drained",
        "area_ha": 7.23
    },
    {
        "soil_code": "RED-01",
        "soil_name": "Red Sandy Soils",
        "texture": "Sandy Loam",
        "drainage_class": "Well Drained",
        "area_ha": 1323.77
    },
    {
        "soil_code": "RED-02",
        "soil_name": "Red Loamy Soils",
        "texture": "Loam",
        "drainage_class": "Well Drained",
        "area_ha": 882.06
    },
    {
        "soil_code": "CAL-01",
        "soil_name": "Calcareous Soils",
        "texture": "Sandy Clay Loam",
        "drainage_class": "Moderately Drained",
        "area_ha": 183.54
    },
    {
        "soil_code": "SAL-01",
        "soil_name": "Saline-Alkaline Soils",
        "texture": "Clay Loam",
        "drainage_class": "Poorly Drained",
        "area_ha": 245.67
    },
    {
        "soil_code": "LAT-01",
        "soil_name": "Laterite Soils",
        "texture": "Gravelly Loam",
        "drainage_class": "Excessively Drained",
        "area_ha": 98.42
    }
]

def update_soil_data():
    """Update existing soil_types records with sample data"""
    supabase = get_supabase_admin()
    
    # Get existing records
    result = supabase.table("soil_types").select("id").execute()
    existing_records = result.data if result.data else []
    
    print(f"Found {len(existing_records)} existing soil_types records")
    
    if not existing_records:
        print("No existing records found. Inserting new records...")
        for soil in SOIL_SAMPLES:
            soil['district'] = 'Krishna'
            result = supabase.table("soil_types").insert(soil).execute()
            print(f"✓ Inserted {soil['soil_code']} - {soil['soil_name']}")
    else:
        # Update existing records
        for i, record in enumerate(existing_records[:len(SOIL_SAMPLES)]):
            soil_data = SOIL_SAMPLES[i]
            result = supabase.table("soil_types").update(soil_data).eq("id", record['id']).execute()
            print(f"✓ Updated record {record['id'][:8]} with {soil_data['soil_code']} - {soil_data['soil_name']}")
    
    # Verify
    result = supabase.table("soil_types").select("soil_code, soil_name, texture, area_ha").limit(5).execute()
    print("\n📊 Sample data after update:")
    for row in result.data:
        print(f"  - {row['soil_code']}: {row['soil_name']} ({row['texture']}) - {row['area_ha']} ha")
    
    print(f"\n✅ Successfully populated {len(SOIL_SAMPLES)} soil type records")

if __name__ == "__main__":
    update_soil_data()
