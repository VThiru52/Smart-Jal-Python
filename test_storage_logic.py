import base64
import io
from PIL import Image
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

def test_storage():
    # 1. Create a dummy image
    img = Image.new('RGB', (100, 100), color = (73, 109, 137))
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    base64_uri = f"data:image/png;base64,{img_str}"
    print(f"Base64 URI length: {len(base64_uri)}")
    
    # 2. Try to store it in Supabase
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    supabase = create_client(url, key)
    
    village_id = "9dafe5ec-a568-49ca-85b7-364ab00fc286"
    test_data = {
        "recommendations": [
            {
                "title": "Test Rec",
                "image": base64_uri
            }
        ]
    }
    
    print(f"Updating DB for village {village_id}...")
    try:
        res = supabase.table("villages").update({
            "recommendations_cache": test_data
        }).eq("id", village_id).execute()
        
        print(f"DB Update SUCCESS: {res.data}")
        
    except Exception as e:
        print(f"DB Update FAILURE: {e}")

if __name__ == "__main__":
    test_storage()
