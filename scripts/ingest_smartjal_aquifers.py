import os
import sys
import pandas as pd
import geopandas as gpd
from typing import List, Dict
from shapely.geometry import MultiPolygon, Polygon

# Add the parent directory to sys.path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.supabase import get_supabase_admin
from dotenv import load_dotenv

load_dotenv()

def ingest_aquifers():
    base_path = 'd:/Smart Jal/backend/database/SmartJal'
    shp_path = os.path.join(base_path, 'Aquifers_Krishna/Aquifers_Krishna.shp')
    
    if not os.path.exists(shp_path):
        print(f"❌ Error: Shapefile not found at {shp_path}")
        return

    print(f"📖 Reading aquifers shapefile: {shp_path}...")
    gdf = gpd.read_file(shp_path)
    
    # Ensure CRS is 4326 (WGS84)
    if gdf.crs != 'epsg:4326':
        print(f"🔄 Projecting to EPSG:4326...")
        gdf = gdf.to_crs('epsg:4326')

    print(f"✅ Loaded {len(gdf)} aquifer zones.")

    supabase = get_supabase_admin()
    
    batch_data = []
    for _, row in gdf.iterrows():
        # Handle potential NaN values
        def clean(val):
            return None if pd.isna(val) else val

        geom = row.geometry
        # Coerce Polygon to MultiPolygon for PostGIS MultiPolygon column compatibility
        if isinstance(geom, Polygon):
            geom = MultiPolygon([geom])

        data = {
            "code": clean(row.get('AQUI_CODE')),
            "type": clean(row.get('Geo_Class')),
            "permeability_factor": clean(row.get('area')),
            "boundary": geom.wkt if geom else None
        }
        batch_data.append(data)

    # Batch insert with retries
    import time
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"🚀 Ingesting to Supabase (Attempt {attempt + 1})...")
            response = supabase.table("aquifers").upsert(batch_data, on_conflict="code").execute()
            print(f"🎉 Successfully ingested {len(batch_data)} aquifers.")
            break
        except Exception as e:
            print(f"⚠️ Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2
                print(f"🔄 Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"❌ Final Error during ingestion: {e}")
                print("💡 Tip: This might be a transient network issue or a large payload. Try running the script again.")

if __name__ == "__main__":
    ingest_aquifers()
