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

def ingest_usecase_mit(batch_size: int = 200):
    """
    Ingest MIT (Monitoring/Intervention/Treatment) zones from UseCase/OKri_MIT.shp
    """
    base_path = 'd:/Smart Jal/backend/database/UseCase'
    shp_path = os.path.join(base_path, 'OKri_MIT.shp')
    
    if not os.path.exists(shp_path):
        print(f"❌ Error: Shapefile not found at {shp_path}")
        return

    print(f"📖 Reading MIT zones shapefile: {shp_path}...")
    gdf = gpd.read_file(shp_path)
    
    # Ensure CRS is 4326 (WGS84)
    if gdf.crs != 'epsg:4326':
        print(f"🔄 Projecting to EPSG:4326...")
        gdf = gdf.to_crs('epsg:4326')

    print(f"✅ Loaded {len(gdf)} MIT zone records.")
    print(f"📋 Columns available: {list(gdf.columns)}")

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
            
            # Calculate area in hectares
            area_ha = (geom.area * 111320 * 111320) / 10000 if geom else None
            
            # Extract priority level
            priority = clean(row.get('PRIORITY')) or clean(row.get('Priority'))
            if priority and isinstance(priority, str):
                # Convert text priority to numeric
                priority_map = {'HIGH': 1, 'MEDIUM': 2, 'LOW': 3, 
                              'High': 1, 'Medium': 2, 'Low': 3}
                priority = priority_map.get(priority, None)
            
            data = {
                "district": "Krishna",
                "mit_code": clean(row.get('MIT_CODE')) or clean(row.get('Mit_Code')) or clean(row.get('CODE')),
                "mit_name": clean(row.get('MIT_NAME')) or clean(row.get('Mit_Name')) or clean(row.get('NAME')),
                "category": clean(row.get('CATEGORY')) or clean(row.get('Category')) or clean(row.get('TYPE')),
                "priority_level": priority,
                "area_ha": area_ha,
                "geom": geom.wkt if geom else None
            }
            batch_data.append(data)

        # Retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                supabase.table("mit_zones").insert(batch_data).execute()
                print(f"📦 Batch {b+1}/{num_batches} ingested ({end}/{total})")
                break
            except Exception as e:
                print(f"⚠️ Attempt {attempt+1} failed for batch {b+1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep((attempt + 1) * 2)
                else:
                    print(f"❌ Failed batch {b+1}")

    print("🎉 MIT zones ingestion complete!")

if __name__ == "__main__":
    ingest_usecase_mit()
