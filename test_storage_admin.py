import base64
import io
from PIL import Image
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

def test_storage_admin():
    # 1. Create a dummy image
    img = Image.new('RGB', (100, 100), color = (73, 109, 137))
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    base64_uri = f"data:image/png;base64,{img_str}"
    
    # 2. Try to store it in Supabase using ADMIN KEY
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not key:
        print("ERROR: SUPABASE_SERVICE_ROLE_KEY not found in .env")
        return
        
    supabase = create_client(url, key)
    
    village_id = "9dafe5ec-a568-49ca-85b7-364ab00fc286"
    test_data = {
        "recommendations": [
            {
                "title": "Base64 Persistence Test",
                "image": base64_uri
            }
        ]
    }
    
    print(f"Updating DB for village {village_id} with ADMIN key...")
    try:
        res = supabase.table("villages").update({
            "recommendations_cache": test_data
        }).eq("id", village_id).execute()
        
        if res.data:
            print(f"DB Update SUCCESS! Updated row ID: {res.data[0]['id']}")
        else:
            print("DB Update returned NO DATA. (Check RLS or existence)")
        
    except Exception as e:
        print(f"DB Update FAILURE: {e}")

if __name__ == "__main__":
    test_storage_admin()
