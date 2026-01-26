
import os
import sys
import random
from app.core.supabase import get_supabase_admin
from dotenv import load_dotenv

# Add the backend directory to the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

def update_pumping_stats():
    print("🔄 Updating Pumping Data with Area & Hours...")
    
    supabase = get_supabase_admin()
    
    # Fetch all pumping data (select * to preserve all fields for upsert)
    print("📥 Fetching existing pumping records...")
    response = supabase.table("pumping_data").select("*").execute()
    
    if not response.data:
        print("❌ No pumping data found.")
        return

    records = response.data
    updates = []
    
    print(f"📊 Processing {len(records)} records...")
    
    for rec in records:
        crop = rec.get("crop_type") or "Unknown"
        consumption = rec.get("water_consumption_m3") or 0
        
        # Logic for Acrage based on Consumption (approx 5000 m3 per acre for Paddy, less for others)
        # This is rough estimation to make numbers look consistent
        water_per_acre = 3000 # default
        
        if "Paddy" in crop or "Rice" in crop:
            water_per_acre = 6000
            hours_range = (6.0, 10.0)
        elif "Cotton" in crop:
            water_per_acre = 4000
            hours_range = (4.0, 7.0)
        elif "Maize" in crop:
            water_per_acre = 3500
            hours_range = (3.0, 6.0)
        elif "Chilies" in crop:
            water_per_acre = 4500
            hours_range = (5.0, 8.0)
        else: # Pulses, etc
            water_per_acre = 2500
            hours_range = (2.0, 5.0)
            
        # Calculate Area
        # If consumption is 0, give small random area
        if consumption > 0:
            area = consumption / water_per_acre
        else:
            area = random.uniform(0.5, 5.0)
            
        # Jitter area
        area = area * random.uniform(0.9, 1.1)
        
        # Hours
        hours = random.uniform(*hours_range)
        
        # Modify the record in place
        rec["area_acres"] = round(area, 2)
        rec["pumping_hours_per_day"] = round(hours, 1)
        
        updates.append(rec)
        
    # Bulk Update (Supabase doesn't support bulk update easily in one go via py client usually, 
    # but `upsert` works if primary key is present)
    
    print("📤 Pushing updates to database...")
    batch_size = 500
    total = len(updates)
    num_batches = (total + batch_size - 1) // batch_size
    
    for b in range(num_batches):
        start = b * batch_size
        end = min((b + 1) * batch_size, total)
        batch = updates[start:end]
        
        try:
            supabase.table("pumping_data").upsert(batch).execute()
            print(f"📦 Batch {b+1}/{num_batches} updated.")
        except Exception as e:
            print(f"⚠️ Batch {b+1} failed: {e}")

    print("✅ Pumping stats updated!")

if __name__ == "__main__":
    update_pumping_stats()
