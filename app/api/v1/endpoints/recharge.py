from fastapi import APIRouter, Depends
from app.services.recharge_service import recharge_service
from app.core.supabase import get_supabase

router = APIRouter()

@router.get("/priorities")
async def get_recharge_priorities(district: str = "Krishna"):
    """Rank villages by recharge priority"""
    return await recharge_service.calculate_recharge_priorities(district)

@router.get("/zones")
async def get_recharge_zones(district: str = "Krishna", supabase = Depends(get_supabase)):
    """Fetch geo-spatial recharge zones from DB"""
    result = supabase.table("recharge_zones").select("*").execute()
    return result.data
