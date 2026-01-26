import os
import sys
from dotenv import load_dotenv

# Ensure we can import app
sys.path.append(os.getcwd())
load_dotenv('.env')

from app.core.supabase import get_supabase_admin

def fix_stations():
    supabase = get_supabase_admin()
    
    print("Fetching piezometers...")
    response = supabase.table("piezometers").select("*").execute()
    piezometers = response.data
    
    if not piezometers:
        print("No piezometers found.")
        return

    print(f"Found {len(piezometers)} piezometers.")
    
    # Pre-fetch villages
    v_response = supabase.table("villages").select("id, name").execute()
    village_map = {v['id']: v['name'] for v in v_response.data}
    
    updated_count = 0
    
    for p in piezometers:
        old_name = p.get('location_name')
        new_name = old_name
        
        # Criteria for fixing
        if not old_name or old_name == "Unknown Station" or old_name == "Unknown Location":
            # Try to build a better name
            village_name = village_map.get(p.get('village_id'))
            
            if village_name:
                new_name = f"{village_name} Station"
            elif p.get('station_code'):
                new_name = f"Station {p['station_code']}"
            else:
                new_name = f"Station {p['id'][:8].upper()}"
                
            if new_name != old_name:
                print(f"Updating ID {p['id']}: '{old_name}' -> '{new_name}'")
                supabase.table("piezometers").update({"location_name": new_name}).eq("id", p['id']).execute()
                updated_count += 1
                
    print(f"Update complete. Fixed {updated_count} stations.")

if __name__ == "__main__":
    fix_stations()
