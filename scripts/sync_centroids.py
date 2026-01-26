
import os
import sys
from app.core.supabase import get_supabase_admin
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

def sync_centroids():
    print("📍 Syncing Centroids from Lat/Long...")
    supabase = get_supabase_admin()
    
    # Fetch villages with coordinates
    villages = supabase.table("villages").select("id, latitude, longitude").execute().data
    print(f"✅ Found {len(villages)} villages.")
    
    for v in villages:
        lat = v.get('latitude')
        lon = v.get('longitude')
        if lat and lon:
            # We can't easily push 'Point(lon lat)' string to 'geometry' column via standard insert
            # if the API expects GeoJSON or PostGIS format. 
            # Best is to use an RPC or just update via SQL.
            # However, Supabase often accepts GeoJSON for geometry columns.
            centroid = {
                "type": "Point",
                "coordinates": [lon, lat]
            }
            try:
                # Attempt to update centroid
                supabase.table("villages").update({"centroid": centroid}).eq("id", v['id']).execute()
            except Exception as e:
                print(f"❌ Failed for {v['id']}: {e}")
                
    print("🎉 Centroid sync complete!")

if __name__ == "__main__":
    sync_centroids()
