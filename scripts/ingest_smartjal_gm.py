import os
import sys
import pandas as pd
import geopandas as gpd
from shapely.geometry import MultiPolygon, Polygon
import time

# Add the parent directory to sys.path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.supabase import get_supabase_admin
from dotenv import load_dotenv

load_dotenv()

def ingest_geomorphology(batch_size: int = 100):
    base_path = 'd:/Smart Jal/backend/database/SmartJal'
    shp_path = os.path.join(base_path, 'GM_Krishna/GM_Krishna.shp')
    
    if not os.path.exists(shp_path):
        print(f"❌ Error: Shapefile not found at {shp_path}")
        return

    print(f"📖 Reading Geomorphology shapefile: {shp_path}...")
    gdf = gpd.read_file(shp_path)
    
    if gdf.crs != 'epsg:4326':
        print(f"🔄 Projecting to EPSG:4326...")
        gdf = gdf.to_crs('epsg:4326')

    print(f"✅ Loaded {len(gdf)} geomorphology zones.")
    supabase = get_supabase_admin()
    
    # Process in batches
    total = len(gdf)
    num_batches = (total + batch_size - 1) // batch_size
    
    for b in range(num_batches):
        start = b * batch_size
        end = min((b + 1) * batch_size, total)
        chunk = gdf.iloc[start:end]
        
        batch_data = []
        for _, row in chunk.iterrows():
            geom = row.geometry
            if isinstance(geom, Polygon):
                geom = MultiPolygon([geom])
            
            batch_data.append({
                "district": "Krishna",
                "description": str(row.get('FIN_DESC') or row.get('DISCRIPTIO')),
                "geom": geom.wkt if geom else None
            })

        # Retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                supabase.table("geomorphology_zones").insert(batch_data).execute()
                print(f"📦 Batch {b+1}/{num_batches} ingested ({end}/{total})")
                break
            except Exception as e:
                print(f"⚠️ Attempt {attempt+1} failed for batch {b+1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep((attempt + 1) * 2)
                else:
                    print(f"❌ Failed batch {b+1}")

    print("🎉 Geomorphology ingestion complete!")

if __name__ == "__main__":
    ingest_geomorphology()
