"""
Script to populate sample data for Groundwater Forecasting feature.
Reads data from Pumping Data.xlsx and WaterLevels_Krishna/master data_updated.xlsx
and populates villages, piezometers, and readings tables.
"""
import os
import sys
import pandas as pd
import datetime
import random
import time

# Add the parent directory to sys.path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.supabase import get_supabase_admin
from dotenv import load_dotenv

load_dotenv()

def normalize_station_code(value):
    """Normalize station codes to string format"""
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

def clean_string(val):
    """Clean string values"""
    if pd.isna(val):
        return None
    text = str(val).strip()
    return text if text and text.lower() != 'nan' else None

def populate_villages_from_pumping_data():
    """Populate villages table from Pumping Data.xlsx"""
    excel_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'database', 'SmartJal', 'Pumping Data.xlsx'
    )
    
    if not os.path.exists(excel_path):
        print(f"❌ Error: Excel file not found at {excel_path}")
        return {}
    
    print(f"📖 Reading villages from: {excel_path}...")
    df = pd.read_excel(excel_path, sheet_name=0)
    
    supabase = get_supabase_admin()
    
    # Get unique villages
    villages = df['Village'].dropna().unique() if 'Village' in df.columns else []
    if len(villages) == 0:
        # Try alternative column names
        for col in df.columns:
            if 'village' in str(col).lower():
                villages = df[col].dropna().unique()
                break
    
    print(f"✅ Found {len(villages)} unique villages in pumping data.")
    
    # Known coordinates for major villages
    known_coords = {
        "Machilipatnam": (16.18, 81.13),
        "Vijayawada": (16.50, 80.64),
        "Gudivada": (16.43, 80.99),
        "Nuzvid": (16.78, 80.84),
        "Jaggayyapeta": (16.89, 80.09),
        "Avanigadda": (16.02, 80.92),
        "Vuyyuru": (16.37, 80.84),
        "Pamarru": (16.33, 80.95),
        "Gannavaram": (16.53, 80.80),
        "Kaikalur": (16.55, 81.20),
        "Tiruvuru": (17.11, 80.61),
        "Nandigama": (16.77, 80.29),
        "Pedana": (16.26, 81.16),
        "Movva": (16.23, 80.99),
        "Challapalli": (16.11, 80.93)
    }
    
    mandals = [
        "Machilipatnam", "Gudivada", "Vijayawada", "Nuzvid", "Gannavaram",
        "Pamarru", "Vuyyuru", "Kaikalur", "Tiruvuru", "Nandigama",
        "Jaggayyapeta", "Avanigadda", "Movva", "Challapalli", "Pedana"
    ]
    
    village_map = {}  # name -> id
    village_data = []
    
    # Fetch existing villages
    existing_resp = supabase.table("villages").select("id, name").execute()
    existing_map = {row["name"].strip().lower(): row["id"] for row in (existing_resp.data or [])}
    
    for village_name in villages:
        if not village_name or pd.isna(village_name):
            continue
            
        village_name = str(village_name).strip()
        norm_name = village_name.lower()
        
        # Check if village already exists
        if norm_name in existing_map:
            village_map[village_name] = existing_map[norm_name]
            continue
        
        # Determine coordinates
        lat, lng = None, None
        for k, coords in known_coords.items():
            if k.lower() in village_name.lower():
                lat, lng = coords
                lat += random.uniform(-0.01, 0.01)
                lng += random.uniform(-0.01, 0.01)
                break
        
        if not lat:
            lat = random.uniform(15.8, 17.1)
            lng = random.uniform(80.1, 81.5)
        
        mandal = random.choice(mandals)
        
        # Use PostGIS WKT format for geometry
        village_data.append({
            "name": village_name,
            "district": "Krishna",
            "sub_district": mandal,
            "mandal": mandal,
            "centroid": f"SRID=4326;POINT({lng} {lat})",
            "population": random.randint(1000, 15000),
            "total_area_ha": round(random.uniform(200.0, 2000.0), 2)
        })
    
    # Insert new villages
    if village_data:
        print(f"📦 Inserting {len(village_data)} new villages...")
        batch_size = 100
        for i in range(0, len(village_data), batch_size):
            batch = village_data[i:i+batch_size]
            try:
                result = supabase.table("villages").insert(batch).execute()
                for row in result.data:
                    village_map[row['name']] = row['id']
                print(f"   Inserted batch {i//batch_size + 1}...")
            except Exception as e:
                print(f"⚠️ Error inserting batch: {e}")
    
    # Fetch all villages again to get complete map
    all_villages_resp = supabase.table("villages").select("id, name").eq("district", "Krishna").execute()
    for row in (all_villages_resp.data or []):
        village_map[row['name']] = row['id']
    
    print(f"✅ Village population complete. Total villages: {len(village_map)}")
    return village_map

def populate_piezometers_and_readings(village_map):
    """Populate piezometers and readings from WaterLevels_Krishna/master data_updated.xlsx"""
    excel_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'database', 'SmartJal', 'WaterLevels_Krishna', 'master data_updated.xlsx'
    )
    
    if not os.path.exists(excel_path):
        print(f"❌ Error: Excel file not found at {excel_path}")
        return
    
    print(f"📖 Reading water level data from: {excel_path}...")
    df = pd.read_excel(excel_path, sheet_name='meta-historical')
    
    # Identify reading columns (date columns)
    reading_cols = []
    for col in df.columns:
        if isinstance(col, datetime.datetime):
            reading_cols.append(col)
        elif isinstance(col, str):
            try:
                dt = pd.to_datetime(col)
                if dt.year >= 1990:
                    reading_cols.append(col)
            except:
                pass
    
    print(f"🔍 Found {len(reading_cols)} historical reading columns.")
    
    supabase = get_supabase_admin()
    
    # Get village name column
    village_col = None
    for col in df.columns:
        if 'village' in str(col).lower() and 'name' in str(col).lower():
            village_col = col
            break
    
    if not village_col:
        print("⚠️ Warning: Could not find village name column. Using station codes only.")
    
    # Process each row (piezometer)
    piezometer_map = {}  # station_code -> piezometer_id
    all_readings = []
    
    print(f"🔄 Processing {len(df)} piezometer records...")
    
    for idx, row in df.iterrows():
        station_code = normalize_station_code(row.get('ID'))
        if not station_code:
            continue
        
        # Check if piezometer already exists
        existing_piezo = supabase.table("piezometers").select("id").eq("station_code", station_code).execute()
        if existing_piezo.data:
            piezometer_map[station_code] = existing_piezo.data[0]['id']
            continue
        
        # Get village name and ID
        village_id = None
        location_name = station_code
        
        if village_col and village_col in df.columns:
            village_name = clean_string(row.get(village_col))
            if village_name:
                location_name = village_name
                # Try to find village in map (case-insensitive)
                for v_name, v_id in village_map.items():
                    if v_name.lower() == village_name.lower():
                        village_id = v_id
                        break
        
        # If village not found, assign to a random village or create a default
        if not village_id and village_map:
            village_id = random.choice(list(village_map.values()))
        
        # Generate coordinates (use village centroid if available, else random)
        lat, lng = None, None
        if village_id:
            village_resp = supabase.table("villages").select("centroid").eq("id", village_id).single().execute()
            if village_resp.data and village_resp.data.get('centroid'):
                # Extract coordinates from PostGIS point
                # Format: {"type":"Point","coordinates":[lng,lat]}
                centroid = village_resp.data['centroid']
                if isinstance(centroid, dict) and 'coordinates' in centroid:
                    lng, lat = centroid['coordinates']
                else:
                    # Try parsing as WKT
                    import re
                    match = re.search(r'POINT\(([\d.]+)\s+([\d.]+)\)', str(centroid))
                    if match:
                        lng, lat = float(match.group(1)), float(match.group(2))
        
        if not lat:
            lat = random.uniform(15.8, 17.1)
            lng = random.uniform(80.1, 81.5)
        
        # Create piezometer with PostGIS WKT format
        piezometer_data = {
            "station_code": station_code,
            "location_name": location_name,
            "village_id": village_id,
            "geom": f"SRID=4326;POINT({lng} {lat})",
            "depth_m": random.uniform(50.0, 200.0),
            "is_active": True
        }
        
        try:
            result = supabase.table("piezometers").insert(piezometer_data).execute()
            if result.data:
                piezometer_id = result.data[0]['id']
                piezometer_map[station_code] = piezometer_id
        except Exception as e:
            print(f"⚠️ Error creating piezometer {station_code}: {e}")
            continue
        
        # Collect readings for this piezometer
        for col in reading_cols:
            val = row[col]
            if pd.isna(val) or val == 'nan':
                continue
            
            try:
                if isinstance(val, str):
                    clean_val = val.replace('..', '.').strip()
                    float_val = float(clean_val)
                else:
                    float_val = float(val)
            except (ValueError, TypeError):
                continue
            
            date_str = pd.to_datetime(col).strftime('%Y-%m-%d')
            
            all_readings.append({
                "piezometer_id": piezometer_map[station_code],
                "water_level_mbgl": float_val,
                "reading_date": date_str
            })
        
        if (idx + 1) % 50 == 0:
            print(f"   Processed {idx + 1}/{len(df)} piezometers...")
    
    print(f"✅ Created/updated {len(piezometer_map)} piezometers.")
    print(f"📊 Collected {len(all_readings)} reading records.")
    
    # Insert readings in batches
    if all_readings:
        print(f"🚀 Inserting readings in batches...")
        batch_size = 1000
        num_batches = (len(all_readings) + batch_size - 1) // batch_size
        
        for i in range(num_batches):
            start = i * batch_size
            end = min((i + 1) * batch_size, len(all_readings))
            batch = all_readings[start:end]
            
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    supabase.table("readings").upsert(
                        batch,
                        on_conflict="piezometer_id,reading_date"
                    ).execute()
                    print(f"   Batch {i+1}/{num_batches} inserted ({end}/{len(all_readings)})")
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        time.sleep((attempt + 1) * 2)
                    else:
                        print(f"⚠️ Failed to insert batch {i+1}: {e}")
    
    print("🎉 Piezometers and readings population complete!")

def main():
    print("=" * 80)
    print("SMART JAL - POPULATE SAMPLE DATA FOR FORECASTING")
    print("=" * 80)
    print()
    
    # Step 1: Populate villages
    print("Step 1: Populating villages from Pumping Data...")
    village_map = populate_villages_from_pumping_data()
    print()
    
    # Step 2: Populate piezometers and readings
    if village_map:
        print("Step 2: Populating piezometers and readings from WaterLevels data...")
        populate_piezometers_and_readings(village_map)
        print()
    else:
        print("⚠️ No villages found. Skipping piezometers and readings.")
    
    print("=" * 80)
    print("🎉 SAMPLE DATA POPULATION COMPLETE!")
    print("=" * 80)
    print()
    print("Next steps:")
    print("1. Verify data in Supabase dashboard")
    print("2. Test the forecasting API endpoint")
    print("3. Check the frontend to see if villages load correctly")

if __name__ == "__main__":
    main()
