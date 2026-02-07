
import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.append(os.getcwd())

from app.services.drought_service import drought_service

async def test_rec_detail():
    village_id = "9dafe5ec-a568-49ca-85b7-364ab00fc286" # Ithavaram (District: KRISHNA)
    rec_title = "Rainwater Harvesting"
    
    print(f"Testing Recommendation Detail for: {village_id}, Title: {rec_title}")
    try:
        data = await drought_service.get_recommendation_detail(village_id, rec_title)
        print("\n--- Recommendation Detail Result ---")
        print(f"Title: {data.get('title')}")
        print(f"Impact: {data.get('impact')}")
        print(f"Content Summary: {data.get('content', {}).get('overview')[:100]}...")
        print(f"Technical Specs: {data.get('content', {}).get('technicalSpecifications')}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_rec_detail())
