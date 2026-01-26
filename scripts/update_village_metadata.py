
import os
import sys
import random
import json
from app.core.supabase import get_supabase_admin
from dotenv import load_dotenv

# Add the backend directory to the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

def update_metadata():
    print("🔄 Updating Village Metadata (Soil, Elevation)...")
    
    supabase = get_supabase_admin()
    
    # Fetch all villages
    print("📥 Fetching all villages...")
    response = supabase.table("villages").select("id, name").execute()
    
    if not response.data:
        print("❌ No villages found.")
        return

    villages = response.data
    print(f"📊 Processing {len(villages)} villages...")
    
    count = 0
    for v in villages:
        v_id = v["id"]
        
        # Synthesize Data
        soil = {
            "soil_name": random.choice(["Alluvial Soil", "Black Cotton Soil", "Red Loyamy Soil", "Coastal Sand"]),
            "texture": random.choice(["Clayey", "Loamy", "Sandy Loam"]),
            "drainage_class": random.choice(["Well Drained", "Moderately Drained", "Poorly Drained"])
        }
        
        elev = {
            "elevation_m": round(random.uniform(5.0, 45.0), 1),
            "distance_km": round(random.uniform(0.1, 5.0), 2)
        }
        
        try:
            supabase.table("villages").update({
                "soil_profile": soil,
                "elevation_data": elev
            }).eq("id", v_id).execute()
            count += 1
            if count % 50 == 0:
                print(f"   Updated {count}...")
        except Exception as e:
            print(f"⚠️ Failed to update {v['name']}: {e}")

    print(f"✅ Metadata updated for {count} villages!")

if __name__ == "__main__":
    update_metadata()
