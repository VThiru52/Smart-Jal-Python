import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(env_path)

from app.core.supabase import get_supabase_admin

def ingest_water_levels():
    file_path = r'd:/Smart Jal/backend/database/SmartJal/WaterLevels_Krishna/master data_updated.xlsx'
    
    if not os.path.exists(file_path):
        print(f"❌ Error: File not found at {file_path}")
        return

    print(f"📖 Reading Excel file...")
    df = pd.read_excel(file_path)
    
    supabase = get_supabase_admin()
    
    def clean(val):
        if pd.isna(val) or val == '' or str(val).strip() == '-' or str(val).strip().lower() == 'nan':
            return None
        return val

    # Find the data columns
    long_col = next((c for c in df.columns if 'Longitude' in str(c)), None)
    if not long_col:
        print("CRITICAL: Could not find Longitude column")
        return

    long_idx = df.columns.get_loc(long_col)
    reading_cols = df.columns[long_idx+1:]
    
    # 1. UPSERT PIEZOMETERS
    print(f"🏗️ Upserting piezometers...")
    piezometers_batch = []
    for idx, row in df.iterrows():
        id_val = clean(row.get('ID'))
        if not id_val: continue
        
        mandal = clean(row.get('Mandal Name'))
        village = clean(row.get('Village Name'))
        lat = clean(row.get(next((c for c in df.columns if 'Latitude' in str(c)), 'Latitude')))
        lon = clean(row.get(next((c for c in df.columns if 'Longitude' in str(c)), 'Longitude')))
        
        piezometers_batch.append({
            "station_code": str(id_val),
            "location_name": str(village),
            "geom": f"SRID=4326;POINT({lon} {lat})" if lat and lon else None,
            "is_active": True 
        })
        
    chunk_size = 100
    for i in range(0, len(piezometers_batch), chunk_size):
        chunk = piezometers_batch[i:i+chunk_size]
        try:
            supabase.table("piezometers").upsert(chunk, on_conflict="station_code").execute()
        except Exception as e:
            print(f"⚠️ Piezometer Error: {e}")

    # 2. FETCH PIEZOMETER MAPPING
    print("🔗 Fetching mapping...")
    p_res = supabase.table("piezometers").select("id, station_code").execute()
    p_map = {str(x['station_code']): x['id'] for x in p_res.data if x['station_code']}
    print(f"✅ Mapped {len(p_map)} stations.")

    # 3. PROCESS READINGS
    all_readings = []
    total_inserted = 0
    
    for idx, row in df.iterrows():
        id_val = clean(row.get('ID'))
        if not id_val: continue
        station_code = str(id_val)
        
        pid = p_map.get(station_code)
        if not pid: continue
        
        for date_col in reading_cols:
            val = row.get(date_col)
            val = clean(val)
            if val is not None:
                try:
                    r_date = date_col
                    if not isinstance(r_date, datetime):
                        r_date = pd.to_datetime(r_date)
                    
                    all_readings.append({
                        "piezometer_id": pid,
                        "reading_date": r_date.strftime("%Y-%m-%d"),
                        "water_level_mbgl": float(val)
                    })
                except:
                    continue
                
                if len(all_readings) >= 1000:
                    try:
                         supabase.table("readings").upsert(all_readings, on_conflict="piezometer_id,reading_date").execute()
                         total_inserted += len(all_readings)
                         print(f"📦 Progress: {total_inserted} readings...")
                    except Exception as e:
                         print(f"⚠️ Batch Error: {e}")
                    all_readings = []

    if all_readings:
        try:
             supabase.table("readings").upsert(all_readings, on_conflict="piezometer_id,reading_date").execute()
             total_inserted += len(all_readings)
        except Exception as e:
             print(f"⚠️ Final Batch Error: {e}")

    print(f"Total readings: {total_inserted}")

if __name__ == "__main__":
    ingest_water_levels()
