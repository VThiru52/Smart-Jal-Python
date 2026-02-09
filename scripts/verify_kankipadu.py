
from app.core.supabase import get_supabase_admin

def verify():
    supabase = get_supabase_admin()
    v_name = 'Kankipadu'
    # 1. Check village
    v_res = supabase.table('villages').select('id, name').ilike('name', v_name).execute()
    if not v_res.data:
        print(f"Village {v_name} not found!")
        return
    
    v_id = v_res.data[0]['id']
    print(f"Village found: {v_name} ({v_id})")
    
    # 2. Check piezometers
    p_res = supabase.table('piezometers').select('*').eq('village_id', v_id).execute()
    print(f"Piezometers count: {len(p_res.data)}")
    for p in p_res.data:
        p_id = p['id']
        # 3. Check readings
        r_count = supabase.table('readings').select('id', count='exact').eq('piezometer_id', p_id).execute()
        print(f"  Piezometer {p_id} ({p.get('location_name', 'N/A')}): {r_count.count} readings")
        
        # 4. Check the specific join used in forecasting service
        join_res = supabase.table('readings').select(
            "reading_date, water_level_mbgl, piezometers!inner(village_id)"
        ).eq("piezometer_id", p_id).execute()
        print(f"  Join query for this p_id: {len(join_res.data)} results")

if __name__ == "__main__":
    verify()
