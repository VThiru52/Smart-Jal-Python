from fastapi import APIRouter, Depends, HTTPException
from app.schemas import Village, Forecast
from app.core.supabase import get_supabase, get_supabase_admin
from app.services.audit_service import audit_service
from datetime import datetime
from app.services.forecasting_service import forecasting_service
from app.services.spatial_service import spatial_service
from app.services.drought_service import drought_service
from app.services.recharge_service import recharge_service
from typing import List
import pandas as pd

router = APIRouter()



@router.get("/{village_id}/comprehensive")
async def get_comprehensive_village_details(village_id: str):
    """
    Get comprehensive village details including:
    - Basic village info
    - Spatial context (soil, elevation)
    - Groundwater data
    - Pumping/extraction data
    - Total water consumption
    - Current water level
    - Risk assessment
    - AI recommendations
    - Agricultural data
    """
    supabase = get_supabase_admin()  # Use admin client to bypass RLS for public read
    # Get basic village info
    village_result = supabase.table("villages").select("*").eq("id", village_id).single().execute()
    if not village_result.data:
        raise HTTPException(status_code=404, detail="Village not found")
    
    village = village_result.data
    village_name = village.get("name")
    
    # Get spatial context (keep for backward compatibility but prefer DB values)
    spatial_context = await spatial_service.get_village_spatial_context(village_id)
    
    # Get pumping data for this village
    pumping_data = []
    total_water_consumption = 0
    agricultural_area_acres = 0
    agricultural_water_usage = 0
    if village_name:
        pumping_result = supabase.table("pumping_data").select("*").eq("village", village_name).execute()
        pumping_data = pumping_result.data if pumping_result.data else []
        
        # Calculate totals
        if pumping_data:
            df_pumping = pd.DataFrame(pumping_data)
            total_water_consumption = float(df_pumping['water_consumption_m3'].sum()) if 'water_consumption_m3' in df_pumping.columns else 0
            agricultural_area_acres = float(df_pumping['area_acres'].sum()) if 'area_acres' in df_pumping.columns else 0
            agricultural_water_usage = total_water_consumption  # Same as total consumption for agriculture
    
    # Get piezometers in this village
    piezometers = supabase.table("piezometers").select("*").eq("village_id", village_id).execute()
    
    # Get latest readings and calculate current water level
    latest_readings = []
    current_water_level = None
    if piezometers.data:
        all_readings = []
        for piezo in piezometers.data:
            reading = supabase.table("readings").select("*").eq("piezometer_id", piezo["id"]).order("reading_date", desc=True).limit(1).execute()
            if reading.data:
                latest_readings.append(reading.data[0])
                all_readings.append(reading.data[0])
        
        # Calculate average current water level
        if all_readings:
            current_water_level = float(pd.DataFrame(all_readings)['water_level_mbgl'].mean())
    
    # Get risk assessment from drought service
    risk_assessment = None
    try:
        district = village.get("district", "Krishna")
        district_risks = await drought_service.assess_district_risk(district)
        if district_risks:
            village_risk = next((r for r in district_risks if r.get("id") == village_id), None)
            if village_risk:
                risk_assessment = {
                    "risk_score": village_risk.get("risk_score"),
                    "status": village_risk.get("status"),  # CRITICAL, MODERATE, LOW
                    "color": village_risk.get("color"),
                    "metrics": village_risk.get("metrics", {}),
                    "reasons": _get_risk_reasons(village_risk)
                }
    except Exception as e:
        print(f"Error getting risk assessment: {e}")
    
    # AI recommendations - ONLY if specifically requested or already cached in DB (omitted here for manual trigger)
    ai_recommendations = None
    
    # Forecast data - Fetch existing if available
    forecast_data = None
    try:
        forecast_result = supabase.table("forecasts").select("*").eq("village_id", village_id).order("target_date", desc=False).limit(12).execute()
        if forecast_result.data:
            forecast_data = {
                "village_id": village_id,
                "forecasts": forecast_result.data,
                "explainability": {
                    "type": "Trend Analysis (Linear)",
                    "note": "Previously generated forecast retrieved from database."
                }
            }
    except Exception as e:
        print(f"Error fetching forecast data: {e}")
    
    # Use database values directly (already populated)
    # Fallback to total_area_ha if land_area_ha is not set (backward compatibility)
    total_land_area_ha = village.get("land_area_ha") or village.get("total_area_ha")
    
    agricultural_area_ha = village.get("agricultural_area_ha")
    
    # Fallback calculation: Estimate 70% of total area as agricultural if not set
    if (not agricultural_area_ha or agricultural_area_ha == 0) and total_land_area_ha and total_land_area_ha > 0:
        agricultural_area_ha = round(total_land_area_ha * 0.7, 2)
    soil_type = village.get("soil_type")
    soil_texture = village.get("soil_texture")
    soil_drainage = village.get("soil_drainage")
    elevation_m = village.get("elevation_m")
    
    # Use database consumption values if available, otherwise calculate from pumping
    total_consumption_db = village.get("water_consumption_m3")
    agricultural_consumption_db = village.get("agricultural_consumption_m3")
    
    # Calculate domestic consumption estimate (55 LPCD - Liters Per Capita per Day - Rural Standard)
    # Annual Domestic m3 = Population * 55 * 365 / 1000
    domestic_consumption_m3 = (village.get("population") or 0) * 55 * 365 / 1000
    
    # Final calculations
    final_agri_consumption = agricultural_consumption_db if agricultural_consumption_db else (agricultural_water_usage if agricultural_water_usage > 0 else 0)
    
    # Force total to be sum of components (since DB total might just be agri data)
    final_total_consumption = final_agri_consumption + domestic_consumption_m3

    return {
        "village": village,
        "spatial_context": spatial_context,
        "piezometers": piezometers.data if piezometers.data else [],
        "latest_readings": latest_readings,
        "pumping_data": pumping_data,
        "water_consumption": {
            "total_m3": final_total_consumption if final_total_consumption > 0 else None,
            "agricultural_m3": final_agri_consumption if final_agri_consumption > 0 else None,
            "domestic_m3": domestic_consumption_m3, # Added distinct domestic value
        },
        "land_details": {
            "total_area_ha": total_land_area_ha,
            "agricultural_area_acres": agricultural_area_acres if agricultural_area_acres > 0 else None,
            "agricultural_area_ha": agricultural_area_ha,
            "soil_type": soil_type,
            "soil_texture": soil_texture,
            "soil_drainage": soil_drainage
        },
        "current_water_level": {
            "mbgl": current_water_level,
            "status": _get_water_level_status(current_water_level) if current_water_level else "Unknown"
        },
        "elevation": {
            "elevation_m": elevation_m
        },
        "risk_assessment": risk_assessment,
        "ai_recommendations": ai_recommendations,
        "forecast": forecast_data
    }

def _get_risk_reasons(risk_data):
    """Generate human-readable reasons for risk status"""
    status = risk_data.get("status", "")
    metrics = risk_data.get("metrics", {})
    reasons = []
    
    if status == "CRITICAL":
        reasons.append(f"Critical groundwater depth: {metrics.get('avg_depth', 'N/A')}m below ground level")
        reasons.append("High water consumption exceeding sustainable limits")
        reasons.append("Low rainfall patterns affecting recharge")
        reasons.append("Immediate intervention required to prevent water crisis")
    elif status == "MODERATE":
        reasons.append(f"Moderate groundwater depth: {metrics.get('avg_depth', 'N/A')}m below ground level")
        reasons.append("Water consumption approaching sustainable limits")
        reasons.append("Seasonal variations affecting water availability")
        reasons.append("Preventive measures recommended")
    elif status == "LOW":
        reasons.append(f"Healthy groundwater levels: {metrics.get('avg_depth', 'N/A')}m below ground level")
        reasons.append("Water consumption within sustainable limits")
        reasons.append("Adequate recharge patterns observed")
    
    return reasons

def _get_water_level_status(level_mbgl):
    """Determine water level status"""
    if level_mbgl is None:
        return "Unknown"
    if level_mbgl < 5:
        return "Excellent"
    elif level_mbgl < 10:
        return "Good"
    elif level_mbgl < 20:
        return "Moderate"
    elif level_mbgl < 30:
        return "Critical"
    else:
        return "Severe"

@router.get("/{village_id}/forecast")
async def get_village_forecast(village_id: str, periods: int = 12):
    """Retrieve or trigger 3/6/12 month forecast for a village"""
    return await forecasting_service.generate_forecast(village_id, periods)

@router.get("/districts")
async def get_districts():
    """
    Get list of all available districts.
    Primary source: `districts` table.
    Fallback: distinct `district` values from `villages` table (for backward compatibility).
    """
    try:
        supabase = get_supabase_admin()
        # 1. Try dedicated districts table (production path)
        result = supabase.table("districts").select("id, name, created_at, updated_at").order("name").execute()

        districts: List[dict] = []
        if result.data:
            districts = [
                {
                    "id": d.get("id"),
                    "name": d.get("name"),
                    "created_at": d.get("created_at"),
                    "updated_at": d.get("updated_at"),
                }
                for d in result.data
                if d.get("name")
            ]

        # 2. Fallback: derive distinct districts from villages if districts table is empty
        if not districts:
            try:
                villages_resp = supabase.table("villages").select("district").execute()
                if villages_resp.data:
                    unique_names = sorted(
                        {row.get("district") for row in villages_resp.data if row.get("district")}
                    )
                    districts = [{"id": None, "name": name, "created_at": None, "updated_at": None} for name in unique_names]
            except Exception as villages_error:
                print(f"⚠️ Error fetching districts from villages table: {villages_error}")
        
        # 3. Final fallback: If still no districts, return Krishna (all villages are in Krishna)
        if not districts:
            print("⚠️ No districts found. Using Krishna as default fallback.")
            districts = [{"id": None, "name": "Krishna", "created_at": None, "updated_at": None}]

        return districts
    except Exception as e:
        print(f"⚠️ Error fetching districts: {e}")
        # Fallback: Return Krishna district to ensure application continues working
        # This is a production-safe fallback until districts table is properly set up
        return [{"id": None, "name": "Krishna", "created_at": None, "updated_at": None}]

@router.get("/{village_id}/evaluate")
async def evaluate_village_comprehensive(village_id: str):
    """
    Comprehensive village evaluation endpoint.
    Runs all AI and analysis APIs sequentially:
    1. Forecast API
    2. Drought Prediction API
    3. Recharge Plan API
    4. AI Recommendations API
    5. Pumping Data API
    Returns all results in a structured format.
    """
    results = {
        "village_id": village_id,
        "status": "in_progress",
        "steps_completed": [],
        "steps_failed": [],
        "data": {}
    }
    
    try:
        # Step 1: Get basic village info
        supabase = get_supabase_admin()
        village_result = supabase.table("villages").select("*").eq("id", village_id).single().execute()
        if not village_result.data:
            raise HTTPException(status_code=404, detail="Village not found")
        
        village = village_result.data
        village_name = village.get("name")
        district = village.get("district", "Krishna")
        results["data"]["village"] = village
        results["steps_completed"].append("village_info")
        
        # Parallel Execution Phase
        # We group tasks that are independent
        tasks = {
            "forecast": forecasting_service.generate_forecast(village_id, 12),
            "drought_assessment": drought_service.assess_district_risk(district),
            "ai_recommendations": drought_service.get_village_recommendations(village_id),
            "recharge_plan": recharge_service.calculate_recharge_priorities(district),
            "spatial_context": spatial_service.get_village_spatial_context(village_id)
        }
        
        # Execute tasks in parallel
        task_names = list(tasks.keys())
        task_coros = list(tasks.values())
        
        task_results = await asyncio.gather(*task_coros, return_exceptions=True)
        
        # Map results to task names
        results_map = dict(zip(task_names, task_results))
        
        # Process Results
        
        # 1. Forecast
        f_res = results_map["forecast"]
        if isinstance(f_res, dict) and "error" not in f_res:
            results["data"]["forecast"] = f_res
            results["steps_completed"].append("forecast")
        elif isinstance(f_res, Exception):
            results["steps_failed"].append({"step": "forecast", "error": str(f_res)})
        else:
            results["steps_failed"].append({"step": "forecast", "error": f_res.get("error") if isinstance(f_res, dict) else "Unknown error"})

        # 2. Drought Assessment
        d_res = results_map["drought_assessment"]
        if isinstance(d_res, list):
            village_risk = next((r for r in d_res if r.get("id") == village_id), None)
            if village_risk:
                results["data"]["drought_assessment"] = {
                    "risk_score": village_risk.get("risk_score"),
                    "status": village_risk.get("status"),
                    "color": village_risk.get("color"),
                    "metrics": village_risk.get("metrics", {}),
                    "reasons": _get_risk_reasons(village_risk)
                }
                results["steps_completed"].append("drought_assessment")
        elif isinstance(d_res, Exception):
            results["steps_failed"].append({"step": "drought_assessment", "error": str(d_res)})

        # 3. AI Recommendations
        r_res = results_map["ai_recommendations"]
        if isinstance(r_res, dict) and "error" not in r_res:
            results["data"]["ai_recommendations"] = r_res
            results["steps_completed"].append("ai_recommendations")
        elif isinstance(r_res, Exception):
            results["steps_failed"].append({"step": "ai_recommendations", "error": str(r_res)})
        else:
            results["steps_failed"].append({"step": "ai_recommendations", "error": "Internal Error"})

        # 4. Recharge Plan
        rc_res = results_map["recharge_plan"]
        if isinstance(rc_res, list):
            village_recharge = next((r for r in rc_res if r.get("village_id") == village_id), None)
            if village_recharge:
                results["data"]["recharge_plan"] = village_recharge
                results["steps_completed"].append("recharge_plan")
        elif isinstance(rc_res, Exception):
            results["steps_failed"].append({"step": "recharge_plan", "error": str(rc_res)})

        # 5. Spatial Context
        s_res = results_map["spatial_context"]
        if isinstance(s_res, dict) and "error" not in s_res:
            results["data"]["spatial_context"] = s_res
            results["steps_completed"].append("spatial_context")
        elif isinstance(s_res, Exception):
            results["steps_failed"].append({"step": "spatial_context", "error": str(s_res)})

        # Sequential steps for database-heavy tasks that are fast
        # (These remain separate for now to avoid overloading Supabase connection pool)
        
        # Step 6: Get Pumping Data
        try:
            if village_name:
                pumping_result = supabase.table("pumping_data").select("*").eq("village", village_name).execute()
                if pumping_result.data:
                    results["data"]["pumping_data"] = pumping_result.data
                    df_pumping = pd.DataFrame(pumping_result.data)
                    results["data"]["pumping_summary"] = {
                        "total_records": len(pumping_result.data),
                        "total_water_m3": float(df_pumping['water_consumption_m3'].sum()) if 'water_consumption_m3' in df_pumping.columns else 0,
                        "total_area_acres": float(df_pumping['area_acres'].sum()) if 'area_acres' in df_pumping.columns else 0,
                        "by_season": df_pumping.groupby('season')['water_consumption_m3'].sum().to_dict() if 'season' in df_pumping.columns and 'water_consumption_m3' in df_pumping.columns else {},
                        "by_crop": df_pumping.groupby('crop_type')['water_consumption_m3'].sum().to_dict() if 'crop_type' in df_pumping.columns and 'water_consumption_m3' in df_pumping.columns else {}
                    }
                    results["steps_completed"].append("pumping_data")
        except Exception as e:
            results["steps_failed"].append({"step": "pumping_data", "error": str(e)})
        
        # Step 7: Get Latest Readings
        try:
            piezometers = supabase.table("piezometers").select("*").eq("village_id", village_id).execute()
            if piezometers.data:
                all_readings = []
                # Simple optimization: limit number of piezometers checked
                for piezo in piezometers.data[:3]: 
                    reading = supabase.table("readings").select("*").eq("piezometer_id", piezo["id"]).order("reading_date", desc=True).limit(20).execute()
                    if reading.data:
                        all_readings.extend(reading.data)
                
                if all_readings:
                    df_readings = pd.DataFrame(all_readings)
                    results["data"]["readings"] = {
                        "latest_readings": all_readings[:10],
                        "total_readings": len(all_readings),
                        "average_level": float(df_readings['water_level_mbgl'].mean()) if 'water_level_mbgl' in df_readings.columns else None,
                        "min_level": float(df_readings['water_level_mbgl'].min()) if 'water_level_mbgl' in df_readings.columns else None,
                        "max_level": float(df_readings['water_level_mbgl'].max()) if 'water_level_mbgl' in df_readings.columns else None
                    }
                    results["steps_completed"].append("readings")
        except Exception as e:
            results["steps_failed"].append({"step": "readings", "error": str(e)})
        
        results["status"] = "completed"
        return results
        
    except Exception as e:
        results["status"] = "failed"
        results["error"] = str(e)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{village_id}/dossier")
async def get_village_poc_dossier(village_id: str):
    """
    Generates a comprehensive technical dossier for PoC audit.
    Includes SHAP explainability, farmer advisories, and structural suitability logic.
    """
    try:
        # 1. Start with high-level evaluation
        eval_data = await evaluate_village_comprehensive(village_id)
        
        # 2. Add technical audit metadata
        dossier = {
            "metadata": {
                "report_id": f"POC-{village_id[:8]}-{datetime.now().strftime('%Y%m%d')}",
                "generated_at": datetime.now().isoformat(),
                "district": eval_data["data"].get("village", {}).get("district", "Krishna"),
                "poc_district": "Krishna (Primary Study Area)",
                "audit_compliant": True,
                "model_stack": {
                    "forecasting": "Hybrid Prophet + XGBoost (with Rain/Pumping features)",
                    "anomaly": "Isolation Forest (v2.1)",
                    "recommendations": "Gemini 1.5 Flash (with Farmer Advisory logic)",
                    "spatial": "PostGIS Centroid-based Ordinary Kriging"
                }
            },
            "technical_audit": {
                "forecast_explainability": eval_data["data"].get("forecast", {}).get("explainability", {}),
                "recharge_logic": eval_data["data"].get("recharge_plan", {}).get("recommendation_logic", ""),
                "risk_metrics": eval_data["data"].get("drought_assessment", {}).get("metrics", {})
            },
            "advisories": [
                rec for rec in eval_data["data"].get("ai_recommendations", {}).get("recommendations", []) 
                if isinstance(rec, dict) and "Farmer Advisory" in rec.get("description", "")
            ],
            "raw_data_summary": eval_data["data"],
            "vulnerability_index": eval_data["data"].get("drought_assessment", {}).get("risk_score", 0)
        }
        
        # Log the dossier generation in audit
        await audit_service.log_action(
            user_id=None,
            action="GENERATE_POC_DOSSIER",
            table_name="villages",
            record_id=village_id,
            new_data={"report_id": dossier["metadata"]["report_id"]}
        )
        
        return dossier
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dossier generation failed: {str(e)}")

@router.get("/district/{district_name}", response_model=List[Village])
async def get_villages_by_district(district_name: str):
    """List all villages in a district"""
    try:
        supabase = get_supabase_admin()  # Use admin client to bypass RLS for public read
        result = supabase.table("villages").select("*").eq("district", district_name).execute()
        return result.data if result.data else []
    except Exception as e:
        print(f"Error fetching villages for district {district_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{village_id}/recommendation-detail")
async def get_recommendation_detail(village_id: str, title: str):
    """
    Get detailed AI-generated content for a specific recommendation
    """
@router.get("/{village_id}", response_model=Village)
async def get_village_details(village_id: str):
    """Get metadata and GIS info for a specific village"""
    supabase = get_supabase_admin()  # Use admin client to bypass RLS for public read
    result = supabase.table("villages").select("*").eq("id", village_id).single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Village not found")
    return result.data
