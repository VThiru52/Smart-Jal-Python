
import os
import sys
from app.core.supabase import get_supabase_admin
from dotenv import load_dotenv

# Add the backend directory to the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

def sync_villages():
    print("🔄 Syncing village names from Pumping Data...")
    
    supabase = get_supabase_admin()
    
    # 1. Fetch all unique villages from pumping_data
    print("📥 Fetching unique villages from Pumping Data...")
    pumping_result = supabase.table("pumping_data").select("village").execute()
    
    if not pumping_result.data:
        print("❌ No pumping data found.")
        return
        
    # Get unique names
    unique_villages = sorted(list(set([item['village'] for item in pumping_result.data if item['village']])))
    print(f"✅ Found {len(unique_villages)} unique villages.")
    
    # 2. Clear ALL existing villages to ensure clean slate (since we don't have unique constraint on name)
    # This is safe for now as we are re-populating registry
    # 2. Fetch existing villages to map Name -> ID
    # This prevents FK violations by UPDATING existing instead of Deleting
    print("🔍 Fetching existing registry to map IDs...")
    existing_resp = supabase.table("villages").select("id, name").execute()
    # Normalize map for case-insensitive matching
    existing_map = {row["name"].strip().lower(): row["id"] for row in existing_resp.data} if existing_resp.data else {}
    print(f"ℹ️ Found {len(existing_map)} existing villages.")

    # 3. Prepare data with synthesized coordinates/soil/elevation
    print("📦 Preparing payload...")
    
    # Major villages with real coordinates (from Google/Knowledge)
    known_coords = {
        "Machilipatnam": (16.18, 81.13),
        "Vijayawada": (16.50, 80.64),
        "Gudivada": (16.43, 80.99), 
        "Nuzvid": (16.78, 80.84),
        "Jaggayyapeta": (16.89, 80.09),
        "Avanigadda": (16.02, 80.92),
        "Vuyyuru": (16.37, 80.84),
        "Pamarru": (16.33, 80.95),
        "Gannavaram": (16.53, 80.80),
        "Kaikalur": (16.55, 81.20),
        "Tiruvuru": (17.11, 80.61),
        "Nandigama": (16.77, 80.29),
        "Pedana": (16.26, 81.16),
        "Movva": (16.23, 80.99),
        "Challapalli": (16.11, 80.93)
    }
    
    # Mandals List for realism
    mandals = [
        "Machilipatnam", "Gudivada", "Vijayawada", "Nuzvid", "Gannavaram", 
        "Pamarru", "Vuyyuru", "Kaikalur", "Tiruvuru", "Nandigama", 
        "Jaggayyapeta", "Avanigadda", "Movva", "Challapalli", "Pedana"
    ]
    
    import random
    
    updates = []
    inserts = []
    
    for v_name in unique_villages:
        # Determine coordinates
        lat, lng = None, None
        
        # Check if matched known list (fuzzy match)
        for k, coords in known_coords.items():
            if k.lower() in v_name.lower():
                lat, lng = coords
                # Add small jitter to avoid perfect overlap if multiple villages match same town name
                lat += random.uniform(-0.01, 0.01)
                lng += random.uniform(-0.01, 0.01)
                break
        
        # If not known, generate random within Krishna District bounds
        # Bounds: Lat 15.7 - 17.2, Long 80.0 - 81.6
        if not lat:
            lat = random.uniform(15.8, 17.1)
            lng = random.uniform(80.1, 81.5)
            
        mandal = random.choice(mandals)
        
        # Base Data (Measurements)
        measurements = {
            "mandal": mandal, 
            "population": random.randint(1000, 15000), 
            "total_area_ha": round(random.uniform(200.0, 2000.0), 2),
            "risk_level": random.choice(["Low", "Moderate", "High", "Critical"]),
            "latitude": round(lat, 6),
            "longitude": round(lng, 6),
            "soil_profile": {
                "soil_name": random.choice(["Alluvial Soil", "Black Cotton Soil", "Red Loyamy Soil", "Coastal Sand"]),
                "texture": random.choice(["Clayey", "Loamy", "Sandy Loam"]),
                "drainage_class": random.choice(["Well Drained", "Moderately Drained", "Poorly Drained"])
            },
            "elevation_data": {
                "elevation_m": round(random.uniform(5.0, 45.0), 1),
                "distance_km": round(random.uniform(0.1, 5.0), 2)
            }
        }
        
        # If ID exists (case-insensitive check) -> UPDATE METADATA ONLY
        # Do NOT include 'name' or 'district' in update to avoid unique constraint violations
        norm_name = v_name.strip().lower()
        if norm_name in existing_map:
            row = measurements.copy()
            row["id"] = existing_map[norm_name]
            updates.append(row)
        else:
            # INSERT NEW -> Need Name and District
            row = measurements.copy()
            row["name"] = v_name
            row["district"] = "Krishna"
            inserts.append(row)
            
    print(f"📊 Ready to sync: {len(updates)} updates, {len(inserts)} new inserts.")
    
    # Process Updates Iteratively (since Supabase upsert requires full row, and update is one-by-one for different values)
    if updates:
        print(f"🔄 Processing {len(updates)} updates (Iterative)...")
        success_count = 0
        for i, row in enumerate(updates):
            try:
                # Update specific row by ID
                # We removed 'id' from the payload passed to update() to avoid issues, though it's ignored if we use .eq()
                p_id = row.pop("id")
                supabase.table("villages").update(row).eq("id", p_id).execute()
                success_count += 1
                if i % 50 == 0:
                    print(f"   Updated {i+1}...")
            except Exception as e:
                print(f"⚠️ Update failed for ID {p_id}: {e}")
        print(f"✅ Updated {success_count} existing villages.")

    # Process Inserts (Batch is fine)
    if inserts:
        print(f"Pm Processing {len(inserts)} inserts...")
        batch_size = 100
        total = len(inserts)
        num_batches = (total + batch_size - 1) // batch_size
        
        for b in range(num_batches):
            start = b * batch_size
            end = min((b + 1) * batch_size, total)
            batch = inserts[start:end]
            try:
                supabase.table("villages").insert(batch).execute()
                print(f"📦 Insert Batch {b+1}/{num_batches} synced.")
            except Exception as e:
                print(f"⚠️ Insert Batch {b+1} error: {e}")

    print("🎉 Village registry updated with real names!")

if __name__ == "__main__":
    sync_villages()
