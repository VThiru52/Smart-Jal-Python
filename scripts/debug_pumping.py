
import os
import sys
from app.core.supabase import get_supabase_admin
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

def debug_pumping():
    print("🔍 Inspecting Pumping Data...")
    supabase = get_supabase_admin()
    
    # 1. Check Columns
    try:
        res = supabase.table("pumping_data").select("*").limit(1).execute()
        if res.data:
            keys = sorted(list(res.data[0].keys()))
            print(f"✅ Columns found ({len(keys)}): {keys}")
        else:
            print("⚠️ Table exists but is empty.")
    except Exception as e:
        print(f"❌ Failed to fetch table info: {e}")
        
    # 2. Test RPC with simple payload
    print("\n🧪 Testing RPC 'ingest_pumping_data'...")
    payload = [{
        "village": "TestVillage",
        "district": "Krishna",
        "mandal": "TestMandal",
        "year": 2024,
        "season": "Rabi",
        "crop_type": "TestCrop",
        "water_consumption_m3": 100.0,
        "area_acres": 10.0,
        "pumping_hours_per_day": 5.0
    }]
    
    try:
        supabase.rpc("ingest_pumping_data", {"payload": payload}).execute()
        print("✅ RPC Execution Successful!")
    except Exception as e:
        print(f"❌ RPC Execution Failed: {e}")

if __name__ == "__main__":
    debug_pumping()
