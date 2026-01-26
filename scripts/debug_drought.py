
import os
import sys
import asyncio
from app.services.drought_service import drought_service
from dotenv import load_dotenv

# Add the backend directory to the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

async def debug_drought():
    print("🐞 Debugging Drought Risk Assessment...")
    
    try:
        results = await drought_service.assess_district_risk("Krishna")
        
        if isinstance(results, list):
            print(f"✅ Assessment successful! Returned {len(results)} records.")
            
            counts = {"CRITICAL": 0, "MODERATE": 0, "LOW": 0}
            for r in results:
                counts[r.get("status", "LOW")] += 1
            
            print(f"📊 Risk Distribution: {counts}")
            
            if results:
                print(f"Sample: {results[0]['name']} - Score: {results[0]['risk_score']} - Status: {results[0]['status']}")
        else:
            print(f"❌ Assessment returned error/dict: {results}")

        # Test Recommendations for the first village
        if results and isinstance(results, list):
            v_id = results[0]['id']
            print(f"\n🔮 Testing Recommendations for {results[0]['name']} ({v_id})...")
            recs = await drought_service.get_village_recommendations(v_id)
            if "recommendations" in recs:
                print(f"✅ Recommendations generated! Count: {len(recs['recommendations'])}")
            else:
                print(f"❌ Failed to get recommendations: {recs}")

    except Exception as e:
        print(f"❌ Test Failed: {e}")

if __name__ == "__main__":
    asyncio.run(debug_drought())
