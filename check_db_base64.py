import os
from supabase import create_client
from dotenv import load_dotenv
import json

load_dotenv()

def check_db_cache():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    supabase = create_client(url, key)
    
    village_id = "9dafe5ec-a568-49ca-85b7-364ab00fc286"
    print(f"Checking DB cache for village: {village_id}")
    
    try:
        res = supabase.table("villages").select("recommendations_cache").eq("id", village_id).execute()
        
        if res.data and res.data[0].get("recommendations_cache"):
            cache = res.data[0]["recommendations_cache"]
            print("SUCCESS: Found recommendations_cache in DB.")
            
            recs = cache.get("recommendations", [])
            print(f"Number of recommendations: {len(recs)}")
            
            for i, rec in enumerate(recs):
                img = rec.get("image", "")
                print(f"Rec {i+1} [{rec.get('title')}]: Image prefix: {img[:50]}...")
                if img.startswith("data:image"):
                    print(f"  -> VALID Base64 image found!")
                elif img.startswith("/static"):
                    print(f"  -> OLD local path found (needs refresh)")
        else:
            print("INFO: No recommendations_cache found for this village.")
            
    except Exception as e:
        print(f"FAILURE: DB query error: {e}")

if __name__ == "__main__":
    check_db_cache()
