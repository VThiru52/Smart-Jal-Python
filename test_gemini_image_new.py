import asyncio
import os
import sys

# Add the project root to sys.path
sys.path.append(os.getcwd())

from dotenv import load_dotenv
load_dotenv()

from app.services.gemini_service import gemini_service

async def test_image_generation():
    print("Testing Gemini Image Generation...")
    prompt = "A high-tech water filtration system in a rural Indian village, sunrise background, realistic drone shot"
    
    try:
        url = await gemini_service.generate_image_from_text(prompt)
        print(f"Generated Image URL: {url}")
        
        if url.startswith("/static/"):
            file_path = os.path.join("app", url.lstrip("/"))
            if os.path.exists(file_path):
                print(f"SUCCESS: Image saved at {file_path}")
            else:
                print(f"FAILURE: Image file not found at {file_path}")
        else:
            print(f"WARNING: Fallback URL returned: {url}")
            
    except Exception as e:
        print(f"FATAL ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_image_generation())
