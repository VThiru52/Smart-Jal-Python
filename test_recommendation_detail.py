
import asyncio
import os
import sys
from dotenv import load_dotenv

# Ensure we can import from 'app'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from app.services.drought_service import drought_service

async def test_recommendation_detail():
    village_id = "4c728dbc-1b13-4dd9-9162-f0e19a791a0e"
    title = "Elevation-Synchronized Percolation Ponds (ES-PP)"
    
    print(f"Testing Recommendation Detail Generation for {title}...")
    try:
        result = await drought_service.get_recommendation_detail(village_id, title)
        
        if "error" in result:
            print(f"ERR Generation Failed: {result['error']}")
        else:
            print("OK Generation Successful!")
            print(f"Title: {result.get('title')}")
            print(f"Type: {result.get('type')}")
            print(f"Impact: {result.get('impact')}")
            print(f"Content Keys: {list(result.get('content', {}).keys())}")
            print(f"Blog Length: {len(result.get('blog', ''))}")
            print(f"Hero Image: {result.get('hero', {}).get('image')}")
            
    except Exception as e:
        print(f"💥 Fatal Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_recommendation_detail())
