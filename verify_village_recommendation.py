import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the current directory to sys.path to import app
sys.path.append(os.getcwd())

load_dotenv()

from app.services.drought_service import drought_service

async def verify_recommendation_flow():
    village_id = "9dafe5ec-a568-49ca-85b7-364ab00fc286" # Ithavaram
    title = "Check Dam Construction"
    
    print(f"Testing full recommendation flow for Village: {village_id}, Title: {title}...")
    
    try:
        result = await drought_service.get_recommendation_detail(village_id, title)
        
        if "error" in result:
            print(f"FAILURE: Service returned error: {result['error']}")
            return

        print("\n--- RESULTS ---")
        print(f"Village ID: {result.get('village_id')}")
        print(f"Title: {result.get('title')}")
        
        hero = result.get('hero', {})
        image_url = hero.get('image', '')
        print(f"Generated Image URL: {image_url}")
        
        if image_url.startswith("/static/generated_images/"):
            file_path = os.path.join("app", image_url.lstrip("/"))
            if os.path.exists(file_path):
                print(f"SUCCESS: Image file exists at {file_path}")
                # Check file size to ensure it's not an empty file
                size = os.path.getsize(file_path)
                print(f"Image File Size: {size} bytes")
            else:
                print(f"FAILURE: Image file NOT found at {file_path}")
        elif "pollinations.ai" in image_url:
            print("WARNING: Gemini failed, using Pollinations fallback.")
        else:
            print(f"WARNING: Unexpected image URL: {image_url}")

    except Exception as e:
        print(f"FAILURE: Unexpected exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_recommendation_flow())
