
import os
import sys
import random
import asyncio
from app.core.supabase import get_supabase_admin
from dotenv import load_dotenv

# Add the backend directory to the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

async def simulate_drought():
    print("🔥 Simulating Drought Scenarios (Critical & Moderate)...")
    
    supabase = get_supabase_admin()
    
    # 1. Fetch Villages
    print("📥 Fetching villages...")
    villages_resp = supabase.table("villages").select("id, name, total_area_ha").execute()
    
    if not villages_resp.data:
        print("❌ No villages found.")
        return

    villages = villages_resp.data
    # Shuffle
    random.shuffle(villages)
    
    # Select Targets
    # 25 Critical, 50 Moderate
    critical_group = villages[:25]
    moderate_group = villages[25:75]
    
    print(f"🎯 Target: {len(critical_group)} Critical, {len(moderate_group)} Moderate.")
    
    # Helper to Ensure Piezometer Exists
    def ensure_piezometer(v_id, v_name):
        # Check unique constraint on piezometer_id
        pz_id_str = f"PZ-{v_name[:3].upper()}-{v_id.split('-')[0][:4]}"
        
        # Try fetch
        res = supabase.table("piezometers").select("id").eq("village_id", v_id).execute()
        if res.data:
            return res.data[0]['id']
        else:
            # Create via RPC to avoid Schema Cache issues
            payload = [{
                "village_id": v_id,
                "piezometer_id": pz_id_str,
                "depth_m": 50.0,
                "is_active": True
            }]
            
            try:
                # Call RPC
                supabase.rpc("ingest_piezometers", {"payload": payload}).execute()
                
                # Fetch back
                res = supabase.table("piezometers").select("id").eq("piezometer_id", pz_id_str).execute()
                if res.data:
                    p_uuid = res.data[0]['id']
                    # NEW: Clear old readings for this piezo to ensure our simulation counts!
                    supabase.table("readings").delete().eq("piezometer_id", p_uuid).execute()
                    return p_uuid
            except Exception as e:
                print(f"   ⚠️ Piezometer creation hiccup via RPC for {v_name}: {e}")
                pass
            return None

    # 2. Inject Critical Data
    print("🔴 Injecting CRITICAL Data (Deep Water + High Consumption)...")
    for v in critical_group:
        v_id = v['id']
        v_name = v['name']
        area = v.get('total_area_ha', 100)
        
        # A. Deep Groundwater (80m - 120m) -> Score ~40 pts
        pz_uuid = ensure_piezometer(v_id, v_name)
        if pz_uuid:
            # Insert Reading via RPC
            payload = [{
                "piezometer_id": pz_uuid,
                "reading_date": "2024-01-01T00:00:00Z",
                "water_level_mbgl": random.uniform(80.0, 110.0)
            }]
            try:
                supabase.rpc("ingest_readings", {"payload": payload}).execute()
            except Exception as e:
                print(f"   ⚠️ Reading insertion error for {v_name}: {e}")
        
        # B. High Consumption -> Score ~30 pts
        try:
            high_consumption = area * random.uniform(35.0, 50.0)
            payload = [{
                "village": v_name, 
                "district": "Krishna",
                "year": 2024,
                "season": "Rabi",
                "crop_type": "Paddy", 
                "water_consumption_m3": high_consumption,
                "area_acres": area * 2.5,
                "pumping_hours_per_day": 12.0
            }]
            supabase.rpc("ingest_pumping_data", {"payload": payload}).execute()
        except Exception as e:
            print(f"   ⚠️ Pumping data update failed for {v_name}: {e}")
        
    # 3. Inject Moderate Data
    print("🟠 Injecting MODERATE Data (Medium Depth + Medium Consumption)...")
    for v in moderate_group:
        v_id = v['id']
        v_name = v['name']
        area = v.get('total_area_ha', 100)
        
        # A. Medium Groundwater (40m - 60m) -> Score ~25 pts
        pz_uuid = ensure_piezometer(v_id, v_name)
        if pz_uuid:
            # Insert Reading via RPC
            payload = [{
                "piezometer_id": pz_uuid,
                "reading_date": "2024-01-01T00:00:00Z",
                "water_level_mbgl": random.uniform(45.0, 65.0)
            }]
            try:
                supabase.rpc("ingest_readings", {"payload": payload}).execute()
            except Exception as e:
                print(f"   ⚠️ Reading insertion error for {v_name}: {e}")
        
        # B. Medium Consumption -> Score ~15 pts
        try:
            med_consumption = area * random.uniform(15.0, 25.0)
            payload = [{
                "village": v_name,
                "district": "Krishna",
                "year": 2024,
                "season": "Rabi",
                "crop_type": "Maize",
                "water_consumption_m3": med_consumption,
                "area_acres": area * 2.5,
                "pumping_hours_per_day": 8.0
            }]
            supabase.rpc("ingest_pumping_data", {"payload": payload}).execute()
        except Exception as e:
             print(f"   ⚠️ Pumping data update failed for {v_name}: {e}")

    print("✅ Simulation Data Injection Complete!")
    print("   Please refresh the Drought Dashboard.")

if __name__ == "__main__":
    asyncio.run(simulate_drought())
