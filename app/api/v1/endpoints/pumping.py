from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.supabase import get_supabase_admin
from typing import Optional, List

router = APIRouter()

@router.get("/data")
async def get_pumping_data(
    district: str = "Krishna",
    village: Optional[str] = None,
    year: Optional[int] = None,
    season: Optional[str] = None,
    supabase = Depends(get_supabase_admin)
):
    """Get pumping/extraction data with optional filters"""
    try:
        query = supabase.table("pumping_data").select("*").eq("district", district)
        
        if village:
            query = query.eq("village", village)
        if year:
            query = query.eq("year", year)
        if season:
            query = query.eq("season", season)
        
        result = query.execute()
        return result.data if result.data else []
    except Exception as e:
        print(f"Error in get_pumping_data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/village/{village_name}")
async def get_pumping_by_village(
    village_name: str,
    supabase = Depends(get_supabase_admin)
):
    """Get pumping data for a specific village"""
    try:
        result = supabase.table("pumping_data").select("*").eq("village", village_name).execute()
        return result.data if result.data else []
    except Exception as e:
        print(f"Error in get_pumping_by_village: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary")
async def get_pumping_summary(
    district: str = "Krishna",
    village: Optional[str] = None,
    supabase = Depends(get_supabase_admin)
):
    """Get aggregated pumping statistics"""
    try:
        # Get pumping data query
        query = supabase.table("pumping_data").select("*").eq("district", district)
        
        # Apply village filter if provided
        if village:
            query = query.eq("village", village)
            
        result = query.execute()
        
        if not result.data:
            return {"message": "No pumping data available"}
        
        import pandas as pd
        df = pd.DataFrame(result.data)
        
        # Calculate summary statistics with safe type conversion
        summary = {
            "total_records": int(len(df)),
            "unique_villages": int(df['village'].nunique()) if 'village' in df.columns else 0,
            "unique_crop_types": int(df['crop_type'].nunique()) if 'crop_type' in df.columns else 0,
            "total_water_consumption_m3": float(df['water_consumption_m3'].sum()) if 'water_consumption_m3' in df.columns else 0.0,
            "avg_water_consumption_m3": float(df['water_consumption_m3'].mean()) if 'water_consumption_m3' in df.columns else 0.0,
            # Group by crop type
            "by_crop": {str(k): float(v) for k, v in df.groupby('crop_type')['water_consumption_m3'].sum().to_dict().items()} if 'crop_type' in df.columns and 'water_consumption_m3' in df.columns else {},
            # Group by season
            "by_season": {str(k): float(v) for k, v in df.groupby('season')['water_consumption_m3'].sum().to_dict().items()} if 'season' in df.columns and 'water_consumption_m3' in df.columns else {},
            # Group by village (Top 20 for performance)
            "by_village": {str(k): float(v) for k, v in df.groupby('village')['water_consumption_m3'].sum().sort_values(ascending=False).head(20).to_dict().items()} if 'village' in df.columns and 'water_consumption_m3' in df.columns else {}
        }
        
        # Calculate District-wide Domestic & Industrial Estimates
        try:
            # Fetch villages to get population
            # If village filter is active, only fetch that village
            v_query = supabase.table("villages").select("population").eq("district", district)
            if village:
                v_query = v_query.eq("name", village) # Assuming village column in pumping_data matches name in villages
            
            v_result = v_query.execute()
            
            if v_result.data:
                total_population = sum([v.get('population', 0) or 0 for v in v_result.data])
                
                # Estimations (Annual)
                # Drinking: 5 LPCD
                drinking_m3 = total_population * 5 * 365 / 1000
                # Household: 50 LPCD
                household_m3 = total_population * 50 * 365 / 1000
                # Industrial: ~5 LPCD
                industrial_m3 = total_population * 5 * 365 / 1000
                
                summary["domestic_usage_m3"] = drinking_m3 + household_m3
                summary["drinking_water_m3"] = drinking_m3
                summary["household_needs_m3"] = household_m3
                summary["industrial_usage_m3"] = industrial_m3
                summary["total_population"] = total_population
                
                # Update total consumption to include non-agricultural
                summary["grand_total_consumption_m3"] = summary["total_water_consumption_m3"] + drinking_m3 + household_m3 + industrial_m3
            else:
                summary["grand_total_consumption_m3"] = summary["total_water_consumption_m3"]

        except Exception as e:
            print(f"Error calculating domestic usage: {e}")
            # Non-blocking, just proceed
        
        return summary
    except Exception as e:
        print(f"Pumping Summary Error: {str(e)}")
        import traceback
        traceback.print_exc()
        # Return empty summary structure instead of 500 if possible, or just raise
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
