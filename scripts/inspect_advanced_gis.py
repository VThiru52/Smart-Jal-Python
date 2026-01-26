import geopandas as gpd
import os
import json

def inspect_advanced_gis():
    base_path = 'd:/Smart Jal/backend/database/SmartJal'
    results = {}
    
    # 1. Geomorphology
    gm_path = os.path.join(base_path, 'GM_Krishna/GM_Krishna.shp')
    if os.path.exists(gm_path):
        gdf = gpd.read_file(gm_path)
        results['Geomorphology'] = {
            'columns': gdf.columns.tolist(),
            'count': len(gdf),
            'sample': gdf.head(5).drop(columns='geometry').to_dict(orient='records'),
            'types': gdf['Origin'].unique().tolist() if 'Origin' in gdf.columns else []
        }
        
    # 2. LULC
    lulc_path = os.path.join(base_path, 'LULC_Krishna/LULC_Krishna1.shp')
    if os.path.exists(lulc_path):
        gdf_lulc = gpd.read_file(lulc_path)
        results['LULC'] = {
            'columns': gdf_lulc.columns.tolist(),
            'count': len(gdf_lulc),
            'sample': gdf_lulc.head(5).drop(columns='geometry').to_dict(orient='records')
        }
    
    with open('d:/Smart Jal/backend/database/advanced_gis_inspection.json', 'w') as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    inspect_advanced_gis()
