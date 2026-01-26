
from app.core.supabase import get_supabase_admin
import os
import sys

def get_rpc_info():
    s = get_supabase_admin()
    # Query for function definition
    sql = """
    SELECT routine_definition 
    FROM information_schema.routines 
    WHERE routine_name = 'get_village_avg_water_levels';
    """
    # Supabase doesn't have a direct 'query' method, but we can use an RPC that runs SQL or just try to see it via a view if it exists.
    # Actually, let's try to just use a simple table query on information_schema if enabled.
    # If not, I'll ask user for the SQL they used.
    # For now, let's just use a direct query to see if it works.
    try:
        res = s.table("readings").select("count(*)").execute()
        print(f"Readings Count: {res.data}")
        
        # Check Lingala-5 specifically
        v_id = 'c11a83df-202e-477d-974f-813bc1ac7694'
        pz = s.table('piezometers').select('id').eq('village_id', v_id).execute().data
        if pz:
            pz_id = pz[0]['id']
            r = s.table('readings').select('*').eq('piezometer_id', pz_id).execute().data
            print(f"Readings for Lingala-5 (Piezo {pz_id}): {r}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_rpc_info()
