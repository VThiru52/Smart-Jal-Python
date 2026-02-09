import pandas as pd
from app.core.supabase import get_supabase_admin
import datetime

def ingest_koduru():
    supabase = get_supabase_admin()
    
    # Load data
    df = pd.read_excel('master data_updated.xlsx', sheet_name='meta-historical')
    koduru_rows = df[df['ID'].isin([10210, 30395])]
    
    print(f"Found {len(koduru_rows)} stations for Koduru")
    
    # 1. Get/Update Village
    v_res = supabase.table("villages").select("id").ilike("name", "Koduru").execute()
    if v_res.data:
        village_id = v_res.data[0]['id']
        print(f"Village Koduru exists with ID: {village_id}")
    else:
        print("Koduru not found! Creating...")
        # Fallback values if not found (though our research says it exists)
        row = koduru_rows.iloc[0]
        village_data = {
            "name": "Koduru",
            "district": "Krishna",
            "mandal": "Koduru",
            "latitude": float(row[[c for c in df.columns if isinstance(c, str) and 'Latitude' in c][0]]),
            "longitude": float(row[[c for c in df.columns if isinstance(c, str) and 'Longitude' in c][0]]),
            "elevation_m": float(row['MSL in meters']),
            "total_area_ha": 800.0,
            "population": 25000,
            "soil_type": "Coastal Alluvium",
            "risk_status": "CRITICAL" # Setting directly as requested
        }
        v_res = supabase.table("villages").insert(village_data).execute()
        village_id = v_res.data[0]['id']

    # 2. Insert Piezometers and Readings
    loc_key = [c for c in df.columns if isinstance(c, str) and 'Location' in c and 'Premises' in c][0]
    depth_key = [c for c in df.columns if isinstance(c, str) and 'Total' in c and 'Depth' in c][0]

    for _, row in koduru_rows.iterrows():
        station_code = str(row['ID'])
        print(f"\nProcessing Station {station_code}...")
        
        # Check if piezo exists
        existing_p = supabase.table("piezometers").select("id").eq("station_code", station_code).execute()
        if existing_p.data:
            piezo_id = existing_p.data[0]['id']
            # Update village_id to ensure it's linked to the correct Koduru
            supabase.table("piezometers").update({"village_id": village_id}).eq("id", piezo_id).execute()
        else:
            piezo_data = {
                "village_id": village_id,
                "location_name": f"{row[loc_key]}",
                "depth_m": float(row[depth_key]),
                "station_code": station_code,
                "is_active": True
            }
            p_res = supabase.table("piezometers").insert(piezo_data).execute()
            piezo_id = p_res.data[0]['id']
        
        # Insert Readings
        readings = []
        for col, val in row.items():
            if isinstance(col, datetime.datetime) and not pd.isna(val):
                readings.append({
                    "piezometer_id": piezo_id,
                    "water_level_mbgl": float(val),
                    "reading_date": col.strftime('%Y-%m-%d')
                })
        
        if readings:
            print(f"Inserting {len(readings)} readings for {station_code}...")
            chunk_size = 50
            for i in range(0, len(readings), chunk_size):
                supabase.table("readings").insert(readings[i:i + chunk_size]).execute()

    # 3. Inject High Consumption Data to Trigger Critical Status
    print("\nInjecting high consumption data for risk escalation...")
    pumping_entries = [
        {
            "district": "Krishna",
            "village": "Koduru",
            "year": 2024,
            "season": "Kharif",
            "crop_type": "Paddy",
            "area_acres": 450.0,
            "pumping_hours_per_day": 8.0,
            "water_consumption_m3": 18500.0, # High consumption
            "structure_type": "Borewell"
        }
    ]
    supabase.table("pumping_data").insert(pumping_entries).execute()

    # 4. Final Forced Update of Village Metadata
    supabase.table("villages").update({
        "risk_status": "CRITICAL",
        "current_risk_score": 88.5,
        "population": 25000,
        "land_area_ha": 800.0,
        "water_consumption_m3": 25000.0 # High total consumption
    }).eq("id", village_id).execute()

    print("\nKoduru setup and risk escalation complete!")

if __name__ == "__main__":
    ingest_koduru()
