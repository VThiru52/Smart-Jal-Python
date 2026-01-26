import pandas as pd
import geopandas as gpd
import os
import json

def inspect_gis():
    base_path = 'd:/Smart Jal/backend/database/SmartJal'
    results = {}
    
    # 1. GTWells
    shp_path = os.path.join(base_path, 'GTWells_Krishna/GTWells/kris.shp')
    if os.path.exists(shp_path):
        gdf = gpd.read_file(shp_path)
        results['GTWells'] = {
            'columns': gdf.columns.tolist(),
            'count': len(gdf),
            'sample': gdf.head(5).drop(columns='geometry').to_dict(orient='records'),
            'geom_type': str(gdf.geometry.iloc[0].geom_type if not gdf.empty else 'N/A')
        }
        
    # 2. Aquifers
    aq_shp = os.path.join(base_path, 'Aquifers_Krishna/Aquifers_Krishna.shp')
    if os.path.exists(aq_shp):
        gdf_aq = gpd.read_file(aq_shp)
        results['Aquifers'] = {
            'columns': gdf_aq.columns.tolist(),
            'count': len(gdf_aq),
            'sample': gdf_aq.head(5).drop(columns='geometry').to_dict(orient='records'),
            'geom_type': str(gdf_aq.geometry.iloc[0].geom_type if not gdf_aq.empty else 'N/A')
        }
    
    # Write to file for easier reading
    with open('d:/Smart Jal/backend/database/gis_inspection.json', 'w') as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    inspect_gis()
