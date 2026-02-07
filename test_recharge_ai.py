
import asyncio
import os
import sys
from dotenv import load_dotenv

# Ensure we can import from 'app'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from app.services.recharge_service import recharge_service

async def test_recharge_ai():
    print("Testing Recharge Priorities with AI Enhancement...")
    try:
        results = await recharge_service.calculate_recharge_priorities("Krishna")
        
        if not results:
            print("No results returned.")
            return

        print(f"Total results: {len(results)}")
        top_5 = results[:5]
        
        for i, res in enumerate(top_5):
            print(f"\nVillage {i+1}: {res['village_name']}")
            print(f"AI Generated: {res.get('is_ai_generated', False)}")
            print("Suggestions:")
            for s in res['suggestions']:
                print(f"  - {s['name']}: {s['advantages'][:50]}...")
                
    except Exception as e:
        print(f"Fatal Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_recharge_ai())
