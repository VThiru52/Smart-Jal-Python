
import os
import sys
import random
from datetime import datetime, timedelta
from shapely.geometry import Point
from app.core.supabase import get_supabase_admin
from dotenv import load_dotenv

# Add the backend directory to the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

def populate_mock_data():
    print("🔄 Populating Mock Piezometers & Readings...")
    
    supabase = get_supabase_admin()
    
    # 1. Fetch Villages to link Piezometers
    print("📥 Fetching villages...")
    villages_resp = supabase.table("villages").select("id, name, latitude, longitude").execute()
    
    if not villages_resp.data:
        print("❌ No villages found. Cannot link piezometers.")
        return

    villages = villages_resp.data
    print(f"✅ Found {len(villages)} villages.")
    
    # 2. Generate Piezometers (1 station per ~3 villages for realism)
    # We select a random subset of villages to have a monitoring station
    selected_villages = random.sample(villages, min(len(villages), 150))
    
    piezometers = []
    
    print(f"🏗️ Generating {len(selected_villages)} piezometer stations...")
    
    for v in selected_villages:
        # Create a station nearby
        p_lat = v['latitude'] + random.uniform(-0.005, 0.005)
        p_lon = v['longitude'] + random.uniform(-0.005, 0.005)
        
        # Use Hex WKB for robust insertion
        point = Point(p_lon, p_lat)
        geom_hex = point.wkb_hex
        
        piezometers.append({
            "village_id": v['id'],
            "piezometer_id": f"PZ-{v['name'][:3].upper()}-{random.randint(100,999)}",
            "depth_m": round(random.uniform(30.0, 100.0), 2),
            "is_active": True,
            # "geom": geom_hex  # Commenting out geom to bypass PGRST204 error and unblock Recharge Plan
        })

    # Bulk Insert Piezometers via RPC (to bypass Schema Cache / Geometry issues)
    try:
        # Prepare payload for RPC (remove geom object if present, or keep if RPC ignores it. 
        # The RPC defined strictly takes village_id, piezometer_id, depth_m, is_active)
        rpc_payload = []
        for p in piezometers:
            rpc_payload.append({
                "village_id": p['village_id'],
                "piezometer_id": p['piezometer_id'],
                "depth_m": p['depth_m'],
                "is_active": p['is_active']
            })
            
        print(f"🚀 Sending {len(rpc_payload)} piezometers to RPC...")
        supabase.rpc("ingest_piezometers", {"payload": rpc_payload}).execute()
        
        # Now fetch them back to get UUIDs for Readings
        print("🔄 Fetching created piezometers to link readings...")
        p_resp = supabase.table("piezometers").select("id, piezometer_id").execute()
        created_piezometers = p_resp.data
        
        if not created_piezometers:
            print("❌ RPC ran but no piezometers found in DB.")
            return

        print(f"✅ Created/Found {len(created_piezometers)} piezometer stations.")
        
    except Exception as e:
        print(f"❌ Failed to insert piezometers via RPC: {e}")
        return

    # 3. Generate Readings (Last 6 months)
    print("💧 Generating historical readings...")
    
    readings = []
    start_date = datetime.now() - timedelta(days=180)
    
    for p in created_piezometers:
        # Simulate a trend (seasonal decline or recharge)
        current_level = random.uniform(5.0, 40.0)
        
        # Generate 1 reading per month for last 6 months
        for i in range(6):
            date = start_date + timedelta(days=i*30)
            
            # Fluctuate level
            current_level += random.uniform(-2.0, 1.5) 
            current_level = max(2.0, min(current_level, 60.0))
            
            readings.append({
                "piezometer_id": p['id'],
                "reading_date": date.isoformat(),
                "water_level_mbgl": round(current_level, 2)
            })
            
    # Bulk Insert Readings
    batch_size = 500
    total = len(readings)
    num_batches = (total + batch_size - 1) // batch_size
    
    print(f"📤 Pushing {total} readings...")
    
    for b in range(num_batches):
        start = b * batch_size
        end = min((b + 1) * batch_size, total)
        batch = readings[start:end]
        try:
            supabase.table("readings").insert(batch).execute()
            print(f"📦 Batch {b+1}/{num_batches} synced.")
        except Exception as e:
            print(f"⚠️ Batch {b+1} error: {e}")

    print("🎉 Mock data population complete!")

if __name__ == "__main__":
    populate_mock_data()
