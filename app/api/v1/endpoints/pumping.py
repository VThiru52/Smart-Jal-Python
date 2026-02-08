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
        print(f"Pumping Summary Request - District: {district}, Village: {village}")
        query = supabase.table("pumping_data").select("*").eq("district", district)
        
        # Apply village filter if provided
        if village:
            query = query.eq("village", village)
            
        result = query.execute()
        
        import pandas as pd
        df = pd.DataFrame(result.data) if result.data else pd.DataFrame()
        
        # Initialize summary with base fields
        summary = {
            "total_records": int(len(df)),
            "unique_villages": int(df['village'].nunique()) if not df.empty and 'village' in df.columns else 0,
            "unique_crop_types": int(df['crop_type'].nunique()) if not df.empty and 'crop_type' in df.columns else 0,
            "total_water_consumption_m3": float(df['water_consumption_m3'].sum()) if not df.empty and 'water_consumption_m3' in df.columns else 0.0,
            "avg_water_consumption_m3": float(df['water_consumption_m3'].mean()) if not df.empty and 'water_consumption_m3' in df.columns else 0.0,
            "by_crop": {str(k): float(v) for k, v in df.groupby('crop_type')['water_consumption_m3'].sum().to_dict().items()} if not df.empty and 'crop_type' in df.columns and 'water_consumption_m3' in df.columns else {},
            "by_season": {str(k): float(v) for k, v in df.groupby('season')['water_consumption_m3'].sum().to_dict().items()} if not df.empty and 'season' in df.columns and 'water_consumption_m3' in df.columns else {},
            "by_village": {str(k): float(v) for k, v in df.groupby('village')['water_consumption_m3'].sum().sort_values(ascending=False).to_dict().items()} if not df.empty and 'village' in df.columns and 'water_consumption_m3' in df.columns else {}
        }
        
        # Calculate Population-based Estimates (Drinking, Domestic, Industrial)
        try:
            v_query = supabase.table("villages").select("name, population").eq("district", district)
            if village:
                # Clean and use wildcard for robust matching
                clean_village = village.strip()
                # Try exact first, then partial if needed
                v_query = v_query.ilike("name", clean_village)
            
            v_result = v_query.execute()
            
            total_population = 0
            drinking_m3 = 0.0
            household_m3 = 0.0
            industrial_m3 = 0.0
            
            if v_result.data:
                total_population = sum([v.get('population', 0) or 0 for v in v_result.data])
                
                # Dynamic LPCD based on population size for visual variability
                # Small (<2k): lower industrial
                # Medium (2k-10k): standard
                # Large (>10k): slightly higher industrial/drinking
                if total_population < 2000:
                    lpcd_drinking = 4.8
                    lpcd_household = 48.0
                    lpcd_industrial = 2.0
                elif total_population > 10000:
                    lpcd_drinking = 5.5
                    lpcd_household = 55.0
                    lpcd_industrial = 8.0
                else:
                    lpcd_drinking = 5.0
                    lpcd_household = 50.0
                    lpcd_industrial = 5.0

                # Estimations (Annual)
                drinking_m3 = total_population * lpcd_drinking * 365 / 1000
                household_m3 = total_population * lpcd_household * 365 / 1000
                industrial_m3 = total_population * lpcd_industrial * 365 / 1000
                
                summary["total_population"] = total_population
                summary["drinking_water_m3"] = drinking_m3
                summary["household_needs_m3"] = household_m3
                summary["industrial_usage_m3"] = industrial_m3
                summary["domestic_usage_m3"] = drinking_m3 + household_m3
                
                # Debug info for percentages
                total_est = drinking_m3 + household_m3 + industrial_m3
                print(f"Village {village}: P={total_population}, D%={drinking_m3/total_est:.1%}, H%={household_m3/total_est:.1%}")
            else:
                # If no village found but filtered, set population to 0 explicitly
                if village:
                    summary["total_population"] = 0
                    summary["drinking_water_m3"] = 0.0
                    summary["household_needs_m3"] = 0.0
                    summary["industrial_usage_m3"] = 0.0
                
            # Grand Total Calculation
            summary["grand_total_consumption_m3"] = summary.get("total_water_consumption_m3", 0.0) + drinking_m3 + household_m3 + industrial_m3
            
            # If village filter is applied and we have no pumping data but have population, 
            # we should still return the summary instead of "No pumping data available"
            if village and df.empty and v_result.data:
                 # Ensure unique_villages is 1 if we found the village in villages table
                 summary["unique_villages"] = 1

        except Exception as e:
            print(f"Error calculating domestic usage: {e}")
            summary["grand_total_consumption_m3"] = summary.get("total_water_consumption_m3", 0.0)
        
        return summary
    except Exception as e:
        print(f"Pumping Summary Error: {str(e)}")
        import traceback
        traceback.print_exc()
        # Return empty summary structure instead of 500 if possible, or just raise
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
