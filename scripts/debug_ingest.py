import os
import sys
import pandas as pd
import geopandas as gpd
from shapely.geometry import MultiPolygon, Polygon

def debug_ingest():
    base_path = 'd:/Smart Jal/backend/database/UseCase'
    shp_path = os.path.join(base_path, 'OKri_Vil.shp')
    
    print(f"Reading {shp_path}...")
    try:
        gdf = gpd.read_file(shp_path)
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    print("File read successfully.")
    
    # Process just one row
    row = gdf.iloc[0]
    print("Processing first row:")
    
    def clean(val):
        return None if pd.isna(val) else val
    
    try:
        geom = row.geometry
        if isinstance(geom, Polygon):
            geom = MultiPolygon([geom])
        
        centroid = geom.centroid if geom else None
        
        # Area logic
        area = clean(row.get('areaha'))  
        if not area and geom:
             area = (geom.area * 111320 * 111320) / 10000
        
        # Name logic
        village_name = clean(row.get('DVNAME')) or clean(row.get('Village')) or \
                      clean(row.get('NAME')) or clean(row.get('name')) or \
                      f"Village_{row.name}"
        
        mandal_name = clean(row.get('DMNAME'))
        v_code = clean(row.get('VCODE'))
        
        data = {
            "name": village_name,
            "district": clean(row.get('DNAME')) or "Krishna",
            "mandal": mandal_name,
            "village_code": str(v_code) if v_code else None,
            "census_code": str(clean(row.get('NHABCODE'))),
            "total_area_ha":  float(area) if area else None,
            "centroid": f"SRID=4326;POINT({row.get('longitude')} {row.get('latitude')})" if row.get('longitude') else "CALC_CENTROID"
        }
        
        print("Processed Data:")
        print(data)
        
    except Exception as e:
        print(f"Error processing row: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_ingest()
