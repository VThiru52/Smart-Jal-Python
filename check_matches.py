from app.core.supabase import get_supabase_admin
import pandas as pd

def check_matches():
    supabase = get_supabase_admin()
    
    # Get all pumping data village names
    p_res = supabase.table("pumping_data").select("village").execute()
    p_names = set(row['village'] for row in p_res.data) if p_res.data else set()
    print(f"Total unique villages in pumping_data: {len(p_names)}")

    # Get all villages table names
    v_res = supabase.table("villages").select("name").execute()
    v_names = set(row['name'] for row in v_res.data) if v_res.data else set()
    print(f"Total unique villages in villages table: {len(v_names)}")

    matches = p_names.intersection(v_names)
    print(f"Total matches: {len(matches)}")
    
    if p_names:
        missing_in_v = p_names - v_names
        print(f"Sample pumping villages missing in villages table: {list(missing_in_v)[:5]}")
    
    if v_names:
        missing_in_p = v_names - p_names
        print(f"Sample villages table villages missing in pumping_data: {list(missing_in_p)[:5]}")

    # Check if a specific village from the user's "4 villages" exists
    # If the user didn't specify, I'll just check some common ones.

if __name__ == "__main__":
    check_matches()
