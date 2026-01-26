"""
Migrate existing village data from JSONB fields to new columns
Extracts soil_profile, elevation_data, and copies total_area_ha
"""
from app.core.supabase import get_supabase_admin

def migrate_existing_data():
    print("🔄 Migrating existing village data to new columns...")
    
    supabase = get_supabase_admin()
    
    # Get all villages
    villages_result = supabase.table("villages").select("*").execute()
    villages = villages_result.data if villages_result.data else []
    
    print(f"📊 Found {len(villages)} villages")
    
    updated_count = 0
    
    for idx, village in enumerate(villages, 1):
        village_id = village["id"]
        village_name = village["name"]
        
        updates = {}
        
        # 1. Extract from soil_profile JSONB
        soil_profile = village.get("soil_profile")
        if soil_profile and isinstance(soil_profile, dict):
            if not village.get("soil_type") and soil_profile.get("soil_name"):
                updates["soil_type"] = soil_profile["soil_name"]
            if not village.get("soil_texture") and soil_profile.get("texture"):
                updates["soil_texture"] = soil_profile["texture"]
            if not village.get("soil_drainage") and soil_profile.get("drainage_class"):
                updates["soil_drainage"] = soil_profile["drainage_class"]
        
        # 2. Extract from elevation_data JSONB
        elevation_data = village.get("elevation_data")
        if elevation_data and isinstance(elevation_data, dict):
            if not village.get("elevation_m") and elevation_data.get("elevation_m"):
                updates["elevation_m"] = float(elevation_data["elevation_m"])
        
        # 3. Copy total_area_ha to land_area_ha
        total_area = village.get("total_area_ha")
        if total_area and not village.get("land_area_ha"):
            updates["land_area_ha"] = float(total_area)
        
        # 4. Calculate agricultural_area_ha (70% of land)
        land_area = updates.get("land_area_ha") or village.get("land_area_ha")
        if land_area and land_area > 0:
            current_agri = village.get("agricultural_area_ha")
            if not current_agri or current_agri == 0:
                updates["agricultural_area_ha"] = round(land_area * 0.7, 2)
        
        # Apply updates
        if updates:
            try:
                supabase.table("villages").update(updates).eq("id", village_id).execute()
                updated_count += 1
                if idx % 50 == 0:
                    print(f"  Progress: {idx}/{len(villages)} villages processed")
            except Exception as e:
                print(f"  ❌ Error updating {village_name}: {e}")
    
    print(f"\n✅ Migration complete! Updated {updated_count}/{len(villages)} villages")
    
    # Show statistics
    villages_result = supabase.table("villages").select("*").execute()
    villages = villages_result.data if villages_result.data else []
    
    stats = {
        "total": len(villages),
        "with_soil_type": sum(1 for v in villages if v.get("soil_type")),
        "with_elevation": sum(1 for v in villages if v.get("elevation_m")),
        "with_land_area": sum(1 for v in villages if v.get("land_area_ha")),
        "with_agri_area": sum(1 for v in villages if v.get("agricultural_area_ha")),
        "with_water": sum(1 for v in villages if v.get("water_consumption_m3")),
    }
    
    print(f"\n📊 Migration Statistics:")
    print(f"   Total villages: {stats['total']}")
    print(f"   With soil type: {stats['with_soil_type']} ({stats['with_soil_type']/stats['total']*100:.1f}%)")
    print(f"   With elevation: {stats['with_elevation']} ({stats['with_elevation']/stats['total']*100:.1f}%)")
    print(f"   With land area: {stats['with_land_area']} ({stats['with_land_area']/stats['total']*100:.1f}%)")
    print(f"   With agri area: {stats['with_agri_area']} ({stats['with_agri_area']/stats['total']*100:.1f}%)")
    print(f"   With water consumption: {stats['with_water']} ({stats['with_water']/stats['total']*100:.1f}%)")

if __name__ == "__main__":
    migrate_existing_data()
