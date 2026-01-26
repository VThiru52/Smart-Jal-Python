import sys
import os
sys.path.append('.')
from app.core.supabase import get_supabase_admin

def debug_insert():
    s = get_supabase_admin()
    
    # Test 1: Minimal insert
    # Note: 'geom' is NOT NULL in schema
    print("Testing minimal insert with geom...")
    data = {
        "station_code": "DEBUG_STATION_1",
        "location_name": "DEBUG_LOCATION",
        "geom": "POINT(80.5 16.5)"
    }
    try:
        res = s.table("piezometers").insert(data).execute()
        print("Test 1 Success:", res.data)
    except Exception as e:
        print("Test 1 Failed:", e)
        print("Error type:", type(e))

    # Test 2: Insert with SRID prefix
    print("\nTesting insert with SRID...")
    data_srid = {
        "station_code": "DEBUG_STATION_2",
        "location_name": "DEBUG_LOCATION",
        "geom": "SRID=4326;POINT(80.5 16.5)"
    }
    try:
        res = s.table("piezometers").insert(data_srid).execute()
        print("Test 2 Success:", res.data)
    except Exception as e:
        print("Test 2 Failed:", e)

    # Test 3: Check RLS or other constraints via a known table
    print("\nChecking villages count again just to be sure...")
    try:
        v_count = s.table("villages").select("*", count="exact").limit(1).execute().count
        print(f"Villages count: {v_count}")
    except Exception as e:
        print(f"Villages check failed: {e}")

if __name__ == "__main__":
    debug_insert()
