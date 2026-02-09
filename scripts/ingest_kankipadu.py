
import pandas as pd
from app.core.supabase import get_supabase_admin
import numpy as np
import datetime

def ingest_mandal_villages(mandal_name):
    supabase = get_supabase_admin()
    
    # Load data
    df = pd.read_excel('master data_updated.xlsx', sheet_name='meta-historical')
    mandal_rows = df[df['Mandal Name'] == mandal_name]
    
    print(f"Found {len(mandal_rows)} villages in {mandal_name} mandal")
    
    for _, row in mandal_rows.iterrows():
        village_name = row['Village Name']
        print(f"\nProcessing {village_name}...")
        
        # 1. Insert Village (Check if exists first)
        existing_v = supabase.table("villages").select("id").ilike("name", village_name).execute()
        if existing_v.data:
            village_id = existing_v.data[0]['id']
            print(f"Village {village_name} already exists with ID: {village_id}")
        else:
            village_data = {
                "name": village_name,
                "district": "Krishna",
                "mandal": mandal_name,
                "latitude": float(row[[c for c in df.columns if isinstance(c, str) and 'Latitude' in c][0]]),
                "longitude": float(row[[c for c in df.columns if isinstance(c, str) and 'Longitude' in c][0]]),
                "elevation_m": float(row['MSL in meters']),
                "total_area_ha": 500.0,
                "population": 15000,
                "soil_type": "Alluvium",
                "risk_status": "MODERATE"
            }
            print(f"Inserting village {village_name}...")
            v_res = supabase.table("villages").insert(village_data).execute()
            village_id = v_res.data[0]['id']
            print(f"Created village ID: {village_id}")
        
        # 2. Insert Piezometer
        loc_key = [c for c in df.columns if isinstance(c, str) and 'Location' in c and 'Premises' in c][0]
        depth_key = [c for c in df.columns if isinstance(c, str) and 'Total' in c and 'Depth' in c][0]
        
        station_code = str(row['ID'])
        existing_p = supabase.table("piezometers").select("id").eq("station_code", station_code).execute()
        
        if existing_p.data:
            piezo_id = existing_p.data[0]['id']
            print(f"Piezometer {station_code} already exists with ID: {piezo_id}")
        else:
            piezo_data = {
                "village_id": village_id,
                "location_name": f"{row[loc_key]}",
                "depth_m": float(row[depth_key]),
                "station_code": station_code,
                "is_active": True
            }
            print(f"Inserting piezometer {station_code}...")
            p_res = supabase.table("piezometers").insert(piezo_data).execute()
            piezo_id = p_res.data[0]['id']
            print(f"Created piezometer ID: {piezo_id}")
        
        # 3. Insert Readings
        readings = []
        for col, val in row.items():
            if isinstance(col, datetime.datetime) and not pd.isna(val):
                readings.append({
                    "piezometer_id": piezo_id,
                    "water_level_mbgl": float(val),
                    "reading_date": col.strftime('%Y-%m-%d')
                })
        
        if readings:
            print(f"Inserting {len(readings)} readings...")
            chunk_size = 50
            for i in range(0, len(readings), chunk_size):
                chunk = readings[i:i + chunk_size]
                supabase.table("readings").insert(chunk).execute()
    
    print("\nMandal ingestion complete!")

if __name__ == "__main__":
    ingest_mandal_villages("Kankipadu")
