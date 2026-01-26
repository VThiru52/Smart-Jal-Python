
import requests
import json
from app.core.supabase import get_supabase_admin

def update_krishna_boundary():
    url = "https://raw.githubusercontent.com/satishvmadala/andhrapradesh_opendata_locations/main/AndhraPradesh_Districts.geojson"
    print(f"Fetching GeoJSON from {url}...")
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        # Find Krishna district
        krishna_feature = None
        for feature in data.get("features", []):
            props = feature.get("properties", {})
            if props.get("district_name") == "Krishna" or props.get("DISTRICT") == "KRISHNA":
                krishna_feature = feature
                break
        
        if not krishna_feature:
            print("Krishna district not found in the GeoJSON file.")
            # Try searching by common name keys
            for feature in data.get("features", []):
                props = feature.get("properties", {})
                if any("Krishna" in str(v) for v in props.values()):
                    krishna_feature = feature
                    print(f"Found potentially matching feature: {props}")
                    break
        
        if krishna_feature:
            geometry = krishna_feature.get("geometry")
            print(f"Found geometry type: {geometry.get('type')}")
            
            # Convert Polygon to MultiPolygon if necessary
            if geometry.get("type") == "Polygon":
                geometry["type"] = "MultiPolygon"
                geometry["coordinates"] = [geometry["coordinates"]]
                print("Converted Polygon to MultiPolygon.")
            
            # Update Supabase
            supabase = get_supabase_admin()
            print("Updating database...")
            res = supabase.table("districts").update({
                "boundary": geometry
            }).eq("name", "Krishna").execute()
            
            if res.data:
                print("Successfully updated Krishna district boundary in the database.")
            else:
                print("Failed to update database. Check if 'Krishna' exists in districts table.")
        else:
            print("Could not find Krishna district GeoJSON.")
            
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    update_krishna_boundary()
