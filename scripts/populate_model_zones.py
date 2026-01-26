"""
Script to populate model_zones table with representative data for Krishna District
"""
from app.core.supabase import get_supabase_admin

# Representative groundwater model zones for Krishna District
MODEL_ZONE_SAMPLES = [
    {
        "zone_name": "Central Alluvial Zone",
        "model_type": "MODFLOW",
        "description": "High transmissivity alluvial aquifer zone with intensive irrigation"
    },
    {
        "zone_name": "Eastern Delta Zone",
        "model_type": "MODFLOW",
        "description": "Krishna delta region with shallow water table and paddy cultivation"
    },
    {
        "zone_name": "Western Upland Zone",
        "model_type": "MODFLOW",
        "description": "Hard rock aquifer zone with moderate groundwater potential"
    },
    {
        "zone_name": "Northern Recharge Zone",
        "model_type": "MODFLOW",
        "description": "Primary recharge area with canal network influence"
    },
    {
        "zone_name": "Southern Mixed Zone",
        "model_type": "MODFLOW",
        "description": "Transition zone between alluvial and hard rock aquifers"
    },
    {
        "zone_name": "Coastal Interface Zone",
        "model_type": "SEAWAT",
        "description": "Saltwater intrusion monitoring zone near coastal boundary"
    },
    {
        "zone_name": "Urban Pumping Zone",
        "model_type": "MODFLOW",
        "description": "High density well zone with urban water supply wells"
    },
    {
        "zone_name": "Agricultural Intensive Zone",
        "model_type": "MODFLOW",
        "description": "Maximum groundwater extraction zone for irrigation"
    }
]

def update_model_zone_data():
    """Update existing model_zones records with sample data"""
    supabase = get_supabase_admin()
    
    # Get existing records
    result = supabase.table("model_zones").select("id, zone_code").execute()
    existing_records = result.data if result.data else []
    
    print(f"Found {len(existing_records)} existing model_zones records")
    
    if not existing_records:
        print("No existing records found.")
        return
    
    # Update existing records
    updated_count = 0
    for i, record in enumerate(existing_records):
        # Use modulo to cycle through sample data if we have more records than samples
        sample_index = i % len(MODEL_ZONE_SAMPLES)
        zone_data = MODEL_ZONE_SAMPLES[sample_index].copy()
        
        # Keep the existing zone_code if it exists, otherwise generate one
        if not record.get('zone_code'):
            zone_data['zone_code'] = f"MZ-{i+1:03d}"
        
        result = supabase.table("model_zones").update(zone_data).eq("id", record['id']).execute()
        
        if result.data:
            updated_count += 1
            print(f"✓ Updated zone {record.get('zone_code', record['id'][:8])} -> {zone_data['zone_name']}")
    
    # Verify
    result = supabase.table("model_zones").select("zone_code, zone_name, model_type, description").limit(5).execute()
    print("\n📊 Sample data after update:")
    for row in result.data:
        print(f"  - {row.get('zone_code', 'N/A')}: {row.get('zone_name', 'N/A')} ({row.get('model_type', 'N/A')})")
    
    print(f"\n✅ Successfully updated {updated_count} model zone records")

if __name__ == "__main__":
    update_model_zone_data()
