
import os
import sys
import asyncio
from app.core.supabase import get_supabase_admin
from dotenv import load_dotenv

# Add the backend directory to the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

async def debug_recharge():
    print("🐞 Debugging Recharge Priorities...")
    
    supabase = get_supabase_admin()
    district = "Krishna"
    
    # 1. Fetch Villages
    print(f"1. Fetching villages for district: '{district}'")
    villages_resp = supabase.table("villages").select("id, name, average_rainfall_mm, population").eq("district", district).execute()
    
    if not villages_resp.data:
        print("❌ No villages found! Check district name casing or table population.")
    else:
        print(f"✅ Found {len(villages_resp.data)} villages.")
        print(f"   Sample: {villages_resp.data[0]}")
        
    # 2. Fetch Readings RPC
    print("\n2. Calling RPC 'get_village_avg_water_levels'...")
    try:
        readings_resp = supabase.rpc("get_village_avg_water_levels", {}).execute()
        if readings_resp.data:
            print(f"✅ RPC returned {len(readings_resp.data)} records.")
        else:
            print("⚠️ RPC returned NO data (Expected if no readings, but logic should handle it).")
    except Exception as e:
        print(f"❌ RPC Failed: {e}")

    # 3. Test Insert into recharge_zones
    print("\n3. Testing INSERT into 'recharge_zones'...")
    if villages_resp.data:
        v_id = villages_resp.data[0]['id']
        test_payload = {
            "village_id": v_id,
            "priority_score": 5.5,
            "suitability_rank": 2,
            "recommendation_logic": "Debug Test"
        }
        try:
            supabase.table("recharge_zones").insert(test_payload).execute()
            print("✅ INSERT successful!")
            # cleanup
            supabase.table("recharge_zones").delete().eq("village_id", v_id).execute()
        except Exception as e:
            print(f"❌ INSERT Failed: {e}")
    else:
        print("⚠️ Skipping INSERT test (No village ID).")

if __name__ == "__main__":
    asyncio.run(debug_recharge())
