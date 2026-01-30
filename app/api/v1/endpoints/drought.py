from fastapi import APIRouter, Depends, HTTPException
from app.services.drought_service import drought_service
from app.core.supabase import get_supabase_admin
from typing import Optional

router = APIRouter()

@router.get("/district/{district}")
async def get_district_drought_risk(district: str = "Krishna"):
    """
    Get drought risk classification for all villages in a district
    """
    try:
        data = await drought_service.assess_district_risk(district)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recommendations/{village_id}")
async def get_village_recommendations(village_id: str):
    """
    Get AI-powered recommendations for a specific village
    """
    try:
        data = await drought_service.get_village_recommendations(village_id)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recommendations/{village_id}/{recommendation_title}")
async def get_recommendation_detail(village_id: str, recommendation_title: str):
    """
    Get AI-powered structured dashboard and blog for a specific recommendation
    """
    try:
        data = await drought_service.get_recommendation_detail(village_id, recommendation_title)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
