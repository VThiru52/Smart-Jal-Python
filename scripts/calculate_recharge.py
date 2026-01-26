
import os
import sys
import asyncio
from app.services.recharge_service import recharge_service
from dotenv import load_dotenv

# Add the backend directory to the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

async def calculate_priorities():
    print("🔄 Calculating Recharge Priorities...")
    
    try:
        # This will fetch villages, readings, calculate scores, and insert into recharge_zones
        results = await recharge_service.calculate_recharge_priorities("Krishna")
        
        if results:
            print(f"✅ Successfully calculated priorities for {len(results)} villages.")
            print(f"🔝 Top Priority: {results[0]['village_name']} (Score: {results[0]['priority_score']})")
        else:
            print("⚠️ No priorities calculated. Check if villages and readings exist.")
            
    except Exception as e:
        print(f"❌ Calculation failed: {e}")

if __name__ == "__main__":
    asyncio.run(calculate_priorities())
