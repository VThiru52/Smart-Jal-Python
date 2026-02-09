
from app.core.supabase import get_supabase_admin
import datetime

def force_koduru_critical():
    supabase = get_supabase_admin()
    v_id = 'ecf4f14e-7273-4a7e-9d81-4e236edd6aca' # The true Koduru (Mandal: Koduru)
    
    print(f"Applying Critical overrides for Koduru ({v_id})...")
    
    # 1. Update Village Metadata (Baseline)
    supabase.table("villages").update({
        "risk_status": "CRITICAL",
        "current_risk_score": 98.0,
        "water_consumption_m3": 75000.0,
        "population": 45000,
        "total_area_ha": 1200.0
    }).eq("id", v_id).execute()
    
    # 2. Inject Deep Water Readings
    pzs = supabase.table("piezometers").select("id").eq("village_id", v_id).execute().data
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    
    new_readings = []
    for p in pzs:
        for i in range(10): 
            new_readings.append({
                "piezometer_id": p['id'],
                "water_level_mbgl": 82.5, # Deeper to ensure score > 70
                "reading_date": today
            })
    
    if new_readings:
        print(f"Injecting {len(new_readings)} deep readings...")
        supabase.table("readings").insert(new_readings).execute()
    
    # 3. Inject Massive Pumping Data
    print("Injecting massive pumping data...")
    supabase.table("pumping_data").insert({
        "district": "Krishna",
        "village": "Koduru",
        "year": 2024,
        "season": "Rabi",
        "crop_type": "Paddy",
        "area_acres": 800.0,
        "water_consumption_m3": 45000.0,
        "structure_type": "Borewell"
    }).execute()

    print("Overrides applied successfully.")

if __name__ == "__main__":
    force_koduru_critical()
