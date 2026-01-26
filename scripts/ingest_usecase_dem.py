import os
import sys
import pandas as pd
import numpy as np
import time

# Add the parent directory to sys.path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.supabase import get_supabase_admin
from dotenv import load_dotenv

load_dotenv()

def ingest_usecase_dem(sample_points: int = 1000):
    """
    Process DEM raster and extract elevation sample points
    Note: Full raster processing requires rasterio. This creates a sample grid.
    For production, consider storing full raster in Supabase Storage and using PostGIS raster.
    """
    try:
        import rasterio
        from rasterio.sample import sample_gen
        
        base_path = 'd:/Smart Jal/backend/database/UseCase'
        
        # Find DEM file (might be .tif, .dem, or other format)
        dem_files = [f for f in os.listdir(base_path) if 'DEM' in f and f.endswith(('.tif', '.tiff', '.dem'))]
        
        if not dem_files:
            print("⚠️ No DEM raster file found. Skipping elevation data ingestion.")
            print("💡 Tip: Place DEM file in UseCase folder or update path in script.")
            return
        
        dem_path = os.path.join(base_path, dem_files[0])
        print(f"📖 Reading DEM raster: {dem_path}...")
        
        with rasterio.open(dem_path) as src:
            print(f"✅ DEM loaded. Shape: {src.shape}, CRS: {src.crs}")
            
            # Create a regular grid of sample points
            bounds = src.bounds
            
            # Generate grid points
            lons = np.linspace(bounds.left, bounds.right, int(np.sqrt(sample_points)))
            lats = np.linspace(bounds.bottom, bounds.top, int(np.sqrt(sample_points)))
            
            xx, yy = np.meshgrid(lons, lats)
            coords = [(x, y) for x, y in zip(xx.ravel(), yy.ravel())]
            
            # Sample elevation values
            samples = list(sample_gen(src, coords))
            
            print(f"✅ Sampled {len(samples)} elevation points.")
            
            supabase = get_supabase_admin()
            
            # Prepare batch data
            batch_data = []
            for (lon, lat), elevation in zip(coords, samples):
                if elevation[0] is not None and not np.isnan(elevation[0]):
                    batch_data.append({
                        "district": "Krishna",
                        "elevation_m": float(elevation[0]),
                        "geom": f"SRID=4326;POINT({lon} {lat})"
                    })
            
            # Insert in batches
            batch_size = 500
            total = len(batch_data)
            num_batches = (total + batch_size - 1) // batch_size
            
            for b in range(num_batches):
                start = b * batch_size
                end = min((b + 1) * batch_size, total)
                chunk = batch_data[start:end]
                
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        supabase.table("elevation_data").insert(chunk).execute()
                        print(f"📦 Batch {b+1}/{num_batches} ingested ({end}/{total})")
                        break
                    except Exception as e:
                        print(f"⚠️ Attempt {attempt+1} failed for batch {b+1}: {e}")
                        if attempt < max_retries - 1:
                            time.sleep((attempt + 1) * 2)
                        else:
                            print(f"❌ Failed batch {b+1}")
            
            print("🎉 DEM elevation data ingestion complete!")
            
    except ImportError:
        print("⚠️ rasterio not installed. Install with: pip install rasterio")
        print("💡 Skipping DEM ingestion. You can run this script later after installing rasterio.")
    except Exception as e:
        print(f"❌ Error processing DEM: {e}")
        print("💡 DEM ingestion skipped. The application will work without elevation data.")

if __name__ == "__main__":
    ingest_usecase_dem()
