"""
Script to populate mit_zones table with representative data for Krishna District
"""
from app.core.supabase import get_supabase_admin

# Representative MIT (Monitoring, Intervention, Treatment) zones for Krishna District
MIT_ZONE_SAMPLES = [
    {
        "mit_name": "Critical Depletion Zone - Vijayawada Urban",
        "category": "Monitoring",
        "priority_level": 1
    },
    {
        "mit_name": "Intensive Irrigation Zone - Pedana",
        "category": "Intervention",
        "priority_level": 2
    },
    {
        "mit_name": "Saltwater Intrusion Risk Zone - Coastal Belt",
        "category": "Treatment",
        "priority_level": 1
    },
    {
        "mit_name": "Overexploitation Zone - Gudivada",
        "category": "Intervention",
        "priority_level": 1
    },
    {
        "mit_name": "Sustainable Management Zone - Kankipadu",
        "category": "Monitoring",
        "priority_level": 3
    },
    {
        "mit_name": "Recharge Enhancement Zone - Jaggayyapeta",
        "category": "Intervention",
        "priority_level": 2
    },
    {
        "mit_name": "Quality Monitoring Zone - Industrial Area",
        "category": "Monitoring",
        "priority_level": 2
    },
    {
        "mit_name": "Aquifer Storage Recovery Zone - Nuzvid",
        "category": "Treatment",
        "priority_level": 3
    }
]

def update_mit_zone_data():
    """Update existing mit_zones records with sample data"""
    supabase = get_supabase_admin()
    
    # Get existing records
    result = supabase.table("mit_zones").select("id, mit_code").execute()
    existing_records = result.data if result.data else []
    
    print(f"Found {len(existing_records)} existing MIT zones records")
    
    if not existing_records:
        print("No existing records found.")
        return
    
    # Update existing records
    updated_count = 0
    for i, record in enumerate(existing_records):
        # Use modulo to cycle through sample data
        sample_index = i % len(MIT_ZONE_SAMPLES)
        mit_data = MIT_ZONE_SAMPLES[sample_index].copy()
        
        # Keep or generate MIT code
        if not record.get('mit_code'):
            mit_data['mit_code'] = f"MIT-{i+1:04d}"
        
        result = supabase.table("mit_zones").update(mit_data).eq("id", record['id']).execute()
        
        if result.data:
            updated_count += 1
            print(f"✓ Updated MIT zone {record.get('mit_code', record['id'][:8])} -> {mit_data['mit_name']}")
    
    # Verify
    result = supabase.table("mit_zones").select("mit_code, mit_name, category, priority_level").limit(5).execute()
    print("\n📊 Sample data after update:")
    for row in result.data:
        print(f"  - {row.get('mit_code', 'N/A')}: {row.get('mit_name', 'N/A')} | {row.get('category', 'N/A')} | Priority: {row.get('priority_level', 'N/A')}")
    
    print(f"\n✅ Successfully updated {updated_count} MIT zone records")

if __name__ == "__main__":
    update_mit_zone_data()
