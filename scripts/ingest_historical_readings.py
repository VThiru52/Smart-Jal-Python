import os
import sys
import pandas as pd
import datetime
import time

# Add the parent directory to sys.path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.supabase import get_supabase_admin
from dotenv import load_dotenv

load_dotenv()

def normalize_station_code(value):
    """
    Normalize station codes so that values like 10207.0, ' 10207 ', or '10207.00' all match the
    station_code stored in Supabase (which is saved as a string without trailing decimals).
    """
    if value is None:
        return None

    text = str(value).strip()
    if not text or text.lower() == 'nan':
        return None

    try:
        numeric = float(text)
        if numeric.is_integer():
            return str(int(numeric))
    except ValueError:
        pass

    return text

def ingest_historical_readings(batch_size: int = 1000):
    excel_path = 'd:/Smart Jal/backend/database/SmartJal/WaterLevels_Krishna/master data_updated.xlsx'
    
    if not os.path.exists(excel_path):
        print(f"❌ Error: Excel file not found at {excel_path}")
        return

    print(f"📖 Reading historical data from: {excel_path}...")
    df = pd.read_excel(excel_path, sheet_name='meta-historical')
    
    # Identify columns that are readings (datetime or parseable as dates)
    reading_cols = []
    for col in df.columns:
        if isinstance(col, datetime.datetime):
            reading_cols.append(col)
        elif isinstance(col, str):
            try:
                # Try to parse strings like '2011-05-01'
                dt = pd.to_datetime(col)
                if dt.year >= 1990:
                    reading_cols.append(col)
            except:
                pass

    print(f"🔍 Found {len(reading_cols)} historical reading columns.")
    
    supabase = get_supabase_admin()
    
    # 1. Fetch Station Mapping (Station Code -> UUID)
    print("🔗 Fetching piezometer mapping from database...")
    stations_res = supabase.table("piezometers").select("id, station_code").execute()
    station_map = {}
    for s in stations_res.data or []:
        normalized = normalize_station_code(s.get('station_code'))
        if normalized:
            station_map[normalized] = s['id']
    print(f"✅ Loaded {len(station_map)} station mappings.")

    all_readings = []
    missing_station_codes = 0
    
    for _, row in df.iterrows():
        excel_id = normalize_station_code(row.get('ID'))
        if not excel_id:
            continue
            
        # Get actual UUID database ID
        uuid_id = station_map.get(excel_id)
        if not uuid_id:
            missing_station_codes += 1
            continue
            
        for col in reading_cols:
            val = row[col]
            if pd.isna(val) or val == 'nan':
                continue
                
            # Robust float conversion for typos like '4..31'
            try:
                if isinstance(val, str):
                    # Remove multiple dots, spaces, or other common typos
                    clean_val = val.replace('..', '.').strip()
                    float_val = float(clean_val)
                else:
                    float_val = float(val)
            except (ValueError, TypeError):
                print(f"⚠️ Warning: Skipping invalid value '{val}' for station {excel_id} on {col}")
                continue
                
            # Convert column name to ISO date string
            date_str = pd.to_datetime(col).strftime('%Y-%m-%d')
            
            all_readings.append({
                "piezometer_id": uuid_id,
                "water_level_mbgl": float_val,
                "reading_date": date_str
            })

    if missing_station_codes:
        print(f"ℹ️ Skipped {missing_station_codes} rows because their station codes were not found in Supabase. Make sure piezometers are ingested first.")

    total_records = len(all_readings)
    print(f"✅ Prepared {total_records} historical reading records.")

    if total_records == 0:
        print("⚠️ No valid records found to ingest.")
        return

    # Batch insert with retries
    num_batches = (total_records + batch_size - 1) // batch_size
    print(f"🚀 Starting ingestion in {num_batches} batches...")

    for i in range(num_batches):
        start = i * batch_size
        end = min((i + 1) * batch_size, total_records)
        chunk = all_readings[start:end]
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                supabase.table("readings").upsert(chunk, on_conflict="piezometer_id,reading_date").execute()
                print(f"📦 Batch {i+1}/{num_batches} processed ({end}/{total_records})")
                break
            except Exception as e:
                print(f"⚠️ Attempt {attempt+1} failed for batch {i+1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep((attempt + 1) * 2)
                else:
                    print(f"❌ Failed to ingest batch {i+1}")

    print("🎉 Historical readings ingestion complete!")

if __name__ == "__main__":
    ingest_historical_readings()
