import os
import sys
import pandas as pd
import geopandas as gpd
from shapely.geometry import MultiPolygon, Polygon
import time

# Add the parent directory to sys.path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
# Explicitly load .env from backend root
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(env_path)

from app.core.supabase import get_supabase_admin

def ingest_usecase_villages(batch_size: int = 100):
    """
    Ingest comprehensive village boundaries from UseCase/OKri_Vil.shp
    This enriches the existing villages table with detailed boundaries and metadata
    """
    base_path = 'd:/Smart Jal/backend/database/UseCase'
    shp_path = os.path.join(base_path, 'OKri_Vil.shp')
    
    if not os.path.exists(shp_path):
        print(f"❌ Error: Shapefile not found at {shp_path}")
        return

    print(f"Reading villages shapefile: {shp_path}...")
    gdf = gpd.read_file(shp_path)
    
    # Ensure CRS is 4326 (WGS84)
    if gdf.crs != 'epsg:4326':
        print(f"Projecting to EPSG:4326...")
        gdf = gdf.to_crs('epsg:4326')

    print(f"Loaded {len(gdf)} village records.")
    print(f"Columns available: {list(gdf.columns)}")

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
            # Handle potential NaN values
            def clean(val):
                return None if pd.isna(val) else val
            
            geom = row.geometry
            # Coerce Polygon to MultiPolygon
            if isinstance(geom, Polygon):
                geom = MultiPolygon([geom])
            
            # Calculate centroid
            centroid = geom.centroid if geom else None
            
            # Calculate area in hectares (from sq meters)
            area_ha = (geom.area * 111320 * 111320) / 10000 if geom else None
            
            # Extract village name (Correct field from inspection: DVNAME)
            village_name = clean(row.get('DVNAME')) or clean(row.get('Village')) or \
                          clean(row.get('NAME')) or clean(row.get('name')) or \
                          f"Village_{row.name}"

            # Extract Mandal (Correct field from inspection: DMNAME)
            mandal_name = clean(row.get('DMNAME')) or clean(row.get('Mandal'))
            
            # Census/Village Code (VCODE)
            v_code = clean(row.get('VCODE'))
            
            # Area (areaha seems to be present)
            area = clean(row.get('areaha'))  
            if not area and geom:
                 # Fallback calc
                 area = (geom.area * 111320 * 111320) / 10000

            data = {
                "name": village_name,
                "district": clean(row.get('DNAME')) or "Krishna", # Use DNAME if avail
                "mandal": mandal_name,
                "village_code": str(v_code) if v_code else None,
                "census_code": str(clean(row.get('NHABCODE'))), # Guessing NHABCODE is useful
                "total_area_ha":  float(area) if area else None,
                "population": None, # Column not present in source
                "boundary": geom.wkt if geom else None,
                "centroid": f"SRID=4326;POINT({row.get('longitude')} {row.get('latitude')})" if row.get('longitude') else (f"SRID=4326;POINT({centroid.x} {centroid.y})" if centroid else None)
            }
            batch_data.append(data)

        # Retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Upsert based on village name and district
                supabase.table("villages").upsert(batch_data, on_conflict="name,district").execute()
                print(f"Batch {b+1}/{num_batches} ingested ({end}/{total})")
                break
            except Exception as e:
                print(f"Attempt {attempt+1} failed for batch {b+1}: {e}")
                
                # Detailed error logging for first failure
                if attempt == 0:
                    import json
                    # Print first item without geometry to avoid spam
                    debug_item = batch_data[0].copy()
                    debug_item['boundary'] = "OMITTED_WKT"
                    print(f"DEBUG PAYLOAD SAMPLE: {debug_item}")
                
                if attempt < max_retries - 1:
                    time.sleep((attempt + 1) * 2)
                else:
                    print(f"Failed batch {b+1}")

    print("Village boundaries ingestion complete!")

if __name__ == "__main__":
    ingest_usecase_villages()
