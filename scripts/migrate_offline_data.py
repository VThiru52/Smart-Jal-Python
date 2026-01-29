import pandas as pd
import sys
import os
from pathlib import Path
from datetime import datetime
import asyncio

# Add backend directory to path to import app modules
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.supabase import get_supabase_admin
from app.core.config import settings

async def migrate_data():
    supabase = get_supabase_admin()
    
    file_path = Path("database/SmartJal/WaterLevels_Krishna/master data_updated.xlsx")
    if not file_path.exists():
        print(f"Error: File not found at {file_path}")
        return

    print("Reading Excel file...")
    df = pd.read_excel(file_path, sheet_name="meta-historical")
    
    # Identify date columns
    date_cols = []
    for col in df.columns:
        if isinstance(col, (datetime, pd.Timestamp)):
            date_cols.append(col)
        else:
            try:
                parsed = pd.to_datetime(col)
                if parsed.year >= 1990:
                    date_cols.append(col)
            except Exception:
                continue
    
    print(f"Found {len(date_cols)} date columns.")
    
    # Cache piezometers to minimize API calls
    print("Fetching existing piezometers...")
    piezos_resp = supabase.table("piezometers").select("id, station_code").execute()
    piezo_map = {str(p["station_code"]): p["id"] for p in piezos_resp.data}
    print(f"Found {len(piezo_map)} existing piezometers in DB.")

    records_to_insert = []
    
    for _, row in df.iterrows():
        station_code = str(row.get("ID"))
        if station_code not in piezo_map:
            print(f"Skipping station {station_code}: Not found in DB")
            continue
            
        piezo_id = piezo_map[station_code]
        
        for col in date_cols:
            val = row.get(col)
            if pd.isna(val):
                continue
                
            try:
                reading_date = pd.to_datetime(col).strftime("%Y-%m-%d")
                water_level = float(val)
                
                records_to_insert.append({
                    "piezometer_id": piezo_id,
                    "reading_date": reading_date,
                    "water_level_mbgl": water_level
                })
            except Exception as e:
                print(f"Error processing value {val} for {station_code} on {col}: {e}")
                continue

    print(f"Prepared {len(records_to_insert)} records for insertion.")
    
    # Batch insert
    batch_size = 1000
    for i in range(0, len(records_to_insert), batch_size):
        batch = records_to_insert[i:i+batch_size]
        try:
            supabase.table("readings").insert(batch).execute()
            print(f"Inserted batch {i // batch_size + 1}/{(len(records_to_insert) + batch_size - 1) // batch_size}")
        except Exception as e:
            print(f"Error inserting batch: {e}")

    print("Migration complete!")

if __name__ == "__main__":
    asyncio.run(migrate_data())
