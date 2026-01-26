from fastapi import APIRouter, Depends, HTTPException
from app.core.supabase import get_supabase_admin
from app.services.spatial_service import spatial_service
from app.services.analysis_service import analysis_service
from typing import Optional

router = APIRouter()

@router.get("/soil/{lat}/{lon}")
async def get_soil_at_location(
    lat: float,
    lon: float,
    supabase = Depends(get_supabase_admin)
):
    """Get soil type at specific coordinates"""
    result = await spatial_service.get_soil_at_location(lat, lon)
    return result

@router.get("/elevation/{lat}/{lon}")
async def get_elevation_at_location(
    lat: float,
    lon: float,
    radius_km: float = 1.0,
    supabase = Depends(get_supabase_admin)
):
    """Get elevation at specific coordinates"""
    result = await spatial_service.get_elevation_at_location(lat, lon, radius_km)
    return result

@router.get("/model-zones")
async def list_model_zones(
    district: str = "Krishna",
    supabase = Depends(get_supabase_admin)
):
    """List all groundwater model zones"""
    result = await spatial_service.get_model_zones(district)
    return result

@router.get("/mit-zones")
async def list_mit_zones(
    district: str = "Krishna",
    priority: Optional[int] = None,
    supabase = Depends(get_supabase_admin)
):
    """List MIT (monitoring/intervention) zones, optionally filtered by priority"""
    result = await spatial_service.get_mit_zones(district, priority)
    return result

@router.get("/aquifers")
async def list_aquifers(
    supabase = Depends(get_supabase_admin)
):
    """List all aquifer zones"""
    result = await spatial_service.get_aquifers()
    return result

@router.get("/bore-wells")
async def list_bore_wells(
    limit: int = 1000,
    supabase = Depends(get_supabase_admin)
):
    """List bore wells with point geometries (limited)"""
    result = await spatial_service.get_bore_wells(limit=limit)
    return result

@router.get("/land-use")
async def list_land_use_zones(
    supabase = Depends(get_supabase_admin)
):
    """List Land Use / Land Cover zones"""
    result = await spatial_service.get_land_use_zones()
    return result

@router.get("/piezometers")
async def list_piezometers(
    supabase = Depends(get_supabase_admin)
):
    """List Piezometer monitoring stations"""
    result = await spatial_service.get_piezometers()
    return result

@router.get("/piezometers/{piezometer_id}/readings")
async def get_piezometer_readings(
    piezometer_id: str,
    supabase = Depends(get_supabase_admin)
):
    """Get water level readings for a specific piezometer"""
    result = await spatial_service.get_piezometer_readings(piezometer_id)
    return result

@router.get("/village/{village_id}/context")
async def get_village_spatial_context(
    village_id: str,
    supabase = Depends(get_supabase_admin)
):
    """Get comprehensive spatial context for a village (soil, elevation, zones)"""
    result = await spatial_service.get_village_spatial_context(village_id)
    return result

@router.get("/soils")
async def list_soil_types(
    district: str = "Krishna",
    supabase = Depends(get_supabase_admin)
):
    """List all soil types in a district"""
    try:
        result = supabase.table("soil_types").select("*").eq("district", district).execute()
        return result.data if result.data else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    """Get AI-driven yield analysis for a piezometer"""
    result = await analysis_service.get_piezometer_ai_analysis(piezometer_id)
    return result

@router.get("/districts/{name}")
async def get_district_boundary(
    name: str,
    supabase = Depends(get_supabase_admin)
):
    """Get district boundary"""
    result = await spatial_service.get_district_boundary(name)
    if not result:
        raise HTTPException(status_code=404, detail="District not found")
    return result

@router.get("/ap-districts")
async def get_ap_districts(
    supabase = Depends(get_supabase_admin)
):
    """Get all Andhra Pradesh districts boundary"""
    result = await spatial_service.get_ap_districts()
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result
