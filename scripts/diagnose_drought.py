
import os
import sys
import asyncio
from app.services.drought_service import drought_service
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

async def diagnose_drought():
    print("🔍 Diagnosing Drought Data...")
    results = await drought_service.assess_district_risk("Krishna")
    
    if "error" in results:
        print(f"❌ Service Error: {results['error']}")
        return

    total = len(results)
    print(f"✅ Total Villages: {total}")
    
    counts = {"CRITICAL": 0, "MODERATE": 0, "LOW": 0}
    no_centroid = 0
    
    for r in results:
        counts[r['status']] += 1
        if not r.get('centroid'):
            no_centroid += 1
            
    print(f"📊 Risk Distribution: {counts}")
    print(f"📍 Missing Centroids: {no_centroid}")
    
    if total > 0:
        print("\n📈 Top 5 Villages by Risk Score:")
        sorted_res = sorted(results, key=lambda x: x['risk_score'], reverse=True)
        for r in sorted_res[:5]:
            print(f"- {r['name']}: Score={r['risk_score']}, Status={r['status']}, Centroid={'Yes' if r['centroid'] else 'No'}")
            print(f"  Metrics: {r['metrics']}")

if __name__ == "__main__":
    asyncio.run(diagnose_drought())
