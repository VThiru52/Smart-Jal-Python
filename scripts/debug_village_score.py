
import os
import sys
import asyncio
import pandas as pd
from app.services.drought_service import drought_service
from app.services.recharge_service import recharge_service
from app.core.supabase import get_supabase_admin
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

async def debug_village_score(v_name):
    print(f"🕵️ Analyzing {v_name}...")
    s = get_supabase_admin()
    
    # 1. Village Info
    v = s.table('villages').select('*').eq('name', v_name).execute().data
    if not v:
        print(f"❌ {v_name} not found in villages table.")
        return
    v = v[0]
    print(f"   Dist: {v['district']}, Area: {v['total_area_ha']}, Pop: {v['population']}")
    
    # 2. Avg Water Level
    rpc_res = s.rpc('get_village_avg_water_levels').execute().data
    v_level = next((r for r in rpc_res if r['village_id'] == v['id']), None)
    avg_depth = v_level['avg_level_mbgl'] if v_level else 15.0
    print(f"   Avg Depth: {avg_depth} (from readings: {v_level['reading_count'] if v_level else 0})")
    
    # 3. Consumption
    p_resp = s.table("pumping_data").select("water_consumption_m3").eq("village", v_name).execute()
    consumption = sum(p['water_consumption_m3'] for p in p_resp.data) if p_resp.data else 0.0
    print(f"   Total Consumption: {consumption}")
    
    # 4. Manual Score Calculation
    depth_score = min((avg_depth / 60.0) * 40, 40)
    rainfall = 850.0 # Default
    rainfall_score = max((1.0 - (rainfall / 1500.0)) * 30, 5)
    area_ha = v.get('total_area_ha', 100) or 100
    intensity = (consumption / (area_ha * 10))
    consumption_score = min(intensity * 10, 30)
    total_score = depth_score + rainfall_score + consumption_score
    
    print(f"   --- Manual Breakdown ---")
    print(f"   Depth Score ({avg_depth}/60 * 40): {depth_score:.2f}")
    print(f"   Rainfall Score (850/1500): {rainfall_score:.2f}")
    print(f"   Consumption Score ({consumption}/({area_ha}*10) * 10): {consumption_score:.2f}")
    print(f"   TOTAL SCORE: {total_score:.2f}")
    
    status = "LOW"
    if total_score > 70: status = "CRITICAL"
    elif total_score > 40: status = "MODERATE"
    print(f"   Final Status: {status}")

if __name__ == "__main__":
    asyncio.run(debug_village_score("Lingala-5"))
