import geopandas as gpd
import os

shp_path = 'd:/Smart Jal/backend/database/UseCase/OKri_Vil.shp'
print(f"Reading {shp_path}...")
try:
    gdf = gpd.read_file(shp_path)
    print("Columns found:")
    for col in gdf.columns:
        print(f" - {col}")
    print("\nFirst 3 rows:")
    print(gdf.head(3).drop(columns='geometry'))
except Exception as e:
    print(f"Error: {e}")
