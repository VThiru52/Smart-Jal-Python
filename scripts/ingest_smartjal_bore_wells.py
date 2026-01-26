import os
import sys
import pandas as pd
import geopandas as gpd
from typing import List, Dict
import math

# Add the parent directory to sys.path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.supabase import get_supabase_admin
from dotenv import load_dotenv

load_dotenv()

def ingest_bore_wells(batch_size: int = 500):
    base_path = 'd:/Smart Jal/backend/database/SmartJal'
    shp_path = os.path.join(base_path, 'GTWells_Krishna/GTWells/kris.shp')
    
    if not os.path.exists(shp_path):
        print(f"❌ Error: Shapefile not found at {shp_path}")
        return

    print(f"📖 Reading shapefile: {shp_path}...")
    gdf = gpd.read_file(shp_path)
    
    # Ensure CRS is 4326 (WGS84)
    if gdf.crs != 'epsg:4326':
        print(f"🔄 Projecting to EPSG:4326...")
        gdf = gdf.to_crs('epsg:4326')

    total_records = len(gdf)
    print(f"✅ Loaded {total_records} records.")

    supabase = get_supabase_admin()
    
    batches = math.ceil(total_records / batch_size)
    print(f"🚀 Starting ingestion in {batches} batches...")

    for i in range(batches):
        start = i * batch_size
        end = min((i + 1) * batch_size, total_records)
        chunk = gdf.iloc[start:end]
        
        batch_data = []
        for _, row in chunk.iterrows():
            # Handle potential NaN values
            def clean(val):
                return None if pd.isna(val) else val

            data = {
                "district": clean(row.get('District_N')),
                "mandal": clean(row.get('Mandal_Nam')),
                "village": clean(row.get('Village_Na')),
                "well_status": clean(row.get('Bore_Well')),
                "well_type": clean(row.get('Well_Type')),
                "depth_m": clean(row.get('Bore_Depth')),
                "pump_capacity_hp": clean(row.get('Pump_Capac')),
                "crop_type": clean(row.get('Crop_Type')),
                "irrigation_type": clean(row.get('Irrigation')),
                "land_extent_acres": clean(row.get('Extant_Lan')),
                # PostGIS format for ST_GeomFromText
                "geom": f"SRID=4326;POINT({row.geometry.x} {row.geometry.y})" if row.geometry else None
            }
            batch_data.append(data)

        # Batch insert to Supabase with retries
        import time
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = supabase.table("bore_wells").insert(batch_data).execute()
                print(f"📦 Batch {i+1}/{batches} processed ({end}/{total_records})")
                break
            except Exception as e:
                print(f"⚠️ Batch {i+1} Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep((attempt + 1) * 2)
                else:
                    print(f"❌ Failed to ingest batch {i+1} after {max_retries} attempts.")

    print("🎉 Ingestion complete!")

if __name__ == "__main__":
    ingest_bore_wells()
