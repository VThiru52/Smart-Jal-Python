import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

def find_valid_village():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    supabase = create_client(url, key)
    
    print("Fetching first 5 villages...")
    try:
        res = supabase.table("villages").select("id, name, district").limit(5).execute()
        print(f"Villages found: {res.data}")
        
        target_id = "9dafe5ec-a568-49ca-85b7-364ab00fc286"
        check = supabase.table("villages").select("id").eq("id", target_id).execute()
        if check.data:
            print(f"Target ID {target_id} EXISTS in DB.")
        else:
            print(f"Target ID {target_id} DOES NOT exist in DB.")
            
    except Exception as e:
        print(f"FAILURE: {e}")

if __name__ == "__main__":
    find_valid_village()
