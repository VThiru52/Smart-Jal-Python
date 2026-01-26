from fastapi import APIRouter, Depends
from app.schemas import Anomaly, RechargeZone
from app.core.supabase import get_supabase, get_supabase_admin
from typing import List

router = APIRouter()

@router.get("/", response_model=List[Anomaly])
async def get_recent_anomalies(limit: int = 50, supabase = Depends(get_supabase_admin)):
    """Get list of recent groundwater anomalies (using admin for bypass)"""
    try:
        # Fallback to application-side join since DB relationship seems missing
        # 1. Fetch anomalies
        result = supabase.table("anomalies").select("*").order("event_date", desc=True).limit(limit).execute()
        anomalies = result.data
        
        if not anomalies:
            return []

        # 2. Fetch related piezometers manually
        p_ids = list(set([a['piezometer_id'] for a in anomalies if a.get('piezometer_id')]))
        
        if p_ids:
            p_res = supabase.table("piezometers").select("id, station_code, location_name").in_("id", p_ids).execute()
            # Create lookup map
            p_map = {p['id']: p for p in p_res.data}
            
            # 3. Attach to anomalies
            for a in anomalies:
                a['piezometers'] = p_map.get(a['piezometer_id'])
                
        return anomalies

    except Exception as e:
        print(f"Error fetching anomalies: {e}")
        return []

@router.get("/recharge/zones", response_model=List[RechargeZone])
async def get_recharge_recommendations(district: str = "Krishna", supabase = Depends(get_supabase)):
    """Identify and rank critical recharge zones"""
    result = supabase.table("recharge_zones").select("*").execute()
    return result.data
