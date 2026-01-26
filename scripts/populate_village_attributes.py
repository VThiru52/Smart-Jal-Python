"""
Data ingestion script to populate village attributes
Fetches data from spatial APIs and updates village records
"""
import asyncio
from app.core.supabase import get_supabase_admin
from app.services.spatial_service import spatial_service
import pandas as pd

async def populate_village_attributes():
    """
    Populate village attributes from various sources:
    1. Fetch soil data and elevation from spatial APIs
    2. Calculate agricultural land area from pumping data
    3. Calculate water consumption from pumping data
    4. Update village records in database
    """
    print("🌾 Starting village attributes population...")
    
    supabase = get_supabase_admin()
    
    # Get all villages
    villages_result = supabase.table("villages").select("*").execute()
    villages = villages_result.data if villages_result.data else []
    
    print(f"📊 Found {len(villages)} villages to process")
    
    updated_count = 0
    errors = []
    
    for idx, village in enumerate(villages, 1):
        village_id = village["id"]
        village_name = village["name"]
        
        print(f"\n[{idx}/{len(villages)}] Processing: {village_name}")
        
        try:
            updates = {}
            
            # 1. Get or calculate lat/lon from centroid
            if not village.get("latitude") and village.get("centroid"):
                # Centroid should already be updated by migration
                pass
            elif village.get("latitude") and village.get("longitude"):
                updates["latitude"] = village["latitude"]
                updates["longitude"] = village["longitude"]
            
            # 2. Fetch spatial context (soil + elevation)
            lat = village.get("latitude")
            lon = village.get("longitude")
            
            if lat and lon:
                try:
                    # Get soil data
                    soil_data = await spatial_service.get_soil_at_location(lat, lon)
                    if soil_data and "error" not in soil_data:
                        updates["soil_type"] = soil_data.get("soil_name")
                        updates["soil_texture"] = soil_data.get("texture")
                        updates["soil_drainage"] = soil_data.get("drain age_class")
                        print(f"  ✓ Soil: {updates.get('soil_type','N/A')}")
                    
                    # Get elevation
                    elevation_data = await spatial_service.get_elevation(lat, lon)
                    if elevation_data and "elevation_m" in elevation_data:
                        updates["elevation_m"] = elevation_data["elevation_m"]
                        print(f"  ✓ Elevation: {updates.get('elevation_m','N/A')} m")
                        
                except Exception as e:
                    print(f"  ⚠️  Spatial data error: {e}")
            
            # 3. Calculate land area and water consumption from pumping data
            try:
                pumping_result = supabase.table("pumping_data").select("*").eq("village", village_name).execute()
                if pumping_result.data:
                    df = pd.DataFrame(pumping_result.data)
                    
                    # Calculate agricultural area
                    if "area_acres" in df.columns:
                        total_acres = df["area_acres"].sum()
                        agricultural_area_ha = total_acres * 0.404686  # Convert acres to hectares
                        updates["agricultural_area_ha"] = round(agricultural_area_ha, 2)
                        print(f"  ✓ Agricultural area: {agricultural_area_ha:.2f} ha ({total_acres:.2f} ac)")
                    
                    # Calculate water consumption
                    if "water_consumption_m3" in df.columns:
                        total_consumption = df["water_consumption_m3"].sum()
                        updates["water_consumption_m3"] = round(total_consumption, 2)
                        updates["agricultural_consumption_m3"] = round(total_consumption, 2)  # Same as total for now
                        print(f"  ✓ Water consumption: {total_consumption:,.2f} m³")
                        
            except Exception as e:
                print(f"  ⚠️  Pumping data error: {e}")
            
            # 4. Update village record
            if updates:
                supabase.table("villages").update(updates).eq("id", village_id).execute()
                updated_count += 1
                print(f"  ✅ Updated {len(updates)} attributes")
            else:
                print(f"  ℹ️  No updates needed")
                
        except Exception as e:
            error_msg = f"{village_name}: {str(e)}"
            errors.append(error_msg)
            print(f"  ❌ Error: {e}")
    
    print(f"\n{'='*60}")
    print(f"✅ Population complete!")
    print(f"   Updated: {updated_count}/{len(villages)} villages")
    
    if errors:
        print(f"\n❌ Errors encountered:")
        for error in errors[:10]:  # Show first 10 errors
            print(f"   - {error}")
        if len(errors) > 10:
            print(f"   ... and {len(errors) - 10} more")
    
    return updated_count, errors

if __name__ == "__main__":
    print("🚀 Village Attributes Population Script")
    print("="*60)
    updated, errors = asyncio.run(populate_village_attributes())
    print(f"\n✨ Done! {updated} villages updated")
