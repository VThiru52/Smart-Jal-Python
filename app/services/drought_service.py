from app.core.supabase import get_supabase_admin
from app.services.spatial_service import spatial_service
from app.services.recharge_service import recharge_service
from app.services.ai_service import ai_service
from typing import List, Dict, Any
import pandas as pd
import numpy as np

class DroughtService:
    def __init__(self):
        self.supabase = get_supabase_admin()

    async def assess_district_risk(self, district: str = "Krishna"):
        """
        Assess drought risk for all villages in a district
        """
        try:
            # 1. Get basic village data
            villages_resp = self.supabase.table("villages").select(
                "id, name, mandal, district, population, total_area_ha, centroid"
            ).eq("district", district).execute()
            
            if not villages_resp.data:
                return []

            # 2. Get recharge priorities (contains avg depth)
            recharge_data = await recharge_service.calculate_recharge_priorities(district)
            depth_map = {r['village_id']: r['avg_depth_mbgl'] for r in recharge_data} if isinstance(recharge_data, list) else {}

            # 3. Get pumping data summary by village
            pumping_resp = self.supabase.table("pumping_data").select("village, water_consumption_m3").execute()
            pumping_map = {}
            if pumping_resp.data:
                p_df = pd.DataFrame(pumping_resp.data)
                p_sum = p_df.groupby('village')['water_consumption_m3'].sum().to_dict()
                pumping_map = p_sum

            results = []
            for v in villages_resp.data:
                v_id = v['id']
                v_name = v['name']
                
                # Fetch components
                avg_depth = depth_map.get(v_id, 15.0)
                rainfall = v.get('average_rainfall_mm', 850.0) or 850.0
                consumption = pumping_map.get(v_name, 0.0)
                
                # Risk Scoring (0-100)
                # Factor 1: Depth (0-40 pts) - Deeper = Riskier
                depth_score = min((avg_depth / 60.0) * 40, 40)
                
                # Factor 2: Rainfall Deficit (0-30 pts) - Lower = Riskier
                rainfall_score = max((1.0 - (rainfall / 1500.0)) * 30, 5)
                
                # Factor 3: Consumption vs Size (0-30 pts)
                area_ha = v.get('total_area_ha', 100) or 100
                intensity = (consumption / (area_ha * 10)) # Rough heuristic
                consumption_score = min(intensity * 10, 30)
                
                total_score = depth_score + rainfall_score + consumption_score
                
                # Classification
                if total_score > 70:
                    status = "CRITICAL"
                    color = "#ef4444" # Red
                elif total_score > 40:
                    status = "MODERATE"
                    color = "#f59e0b" # Orange/Yellow
                else:
                    status = "LOW"
                    color = "#10b981" # Green

                results.append({
                    "id": v_id,
                    "name": v_name,
                    "mandal": v['mandal'],
                    "risk_score": round(total_score, 2),
                    "status": status,
                    "color": color,
                    "metrics": {
                        "avg_depth": round(avg_depth, 2),
                        "rainfall": rainfall,
                        "consumption": consumption
                    },
                    "centroid": v['centroid']
                })

            return results
        except Exception as e:
            print(f"Error in assess_district_risk: {e}")
            return {"error": str(e)}

    async def get_village_recommendations(self, village_id: str):
        """
        AI-driven intervention recommendations based on local characteristics using Gemini
        """
        try:
            # Get spatial context (soil, elevation)
            context = await spatial_service.get_village_spatial_context(village_id)
            if "error" in context:
                return context

            village = context['village']
            soil = context.get('soil', {})
            elevation = context.get('elevation', {})
            
            # Prepare context for AI
            # Get risk status dynamically
            risk_status = "MODERATE"
            try:
                district = village.get("district", "Krishna")
                # Normalize district for query
                normalized_district = district.capitalize()
                district_risks = await self.assess_district_risk(normalized_district)
                
                # If not found with capitalized, try UPPERCASE
                if not district_risks or "error" in district_risks:
                    district_risks = await self.assess_district_risk(district.upper())
                
                if district_risks and isinstance(district_risks, list):
                    v_risk = next((r for r in district_risks if r.get("id") == village_id), None)
                    if v_risk:
                        risk_status = v_risk.get("status", "MODERATE")
            except:
                pass

            ai_context = {
                "village": village,
                "soil": soil,
                "elevation": elevation,
                "risk_context": {
                    "status": risk_status,
                    "rainfall": village.get('average_rainfall_mm') or 850.0
                }
            }
            
            recommendations = await ai_service.generate_water_recommendations(ai_context)

            return {
                "village_id": village_id,
                "village_name": village['name'],
                "risk_context": ai_context['risk_context'],
                "recommendations": recommendations
            }
        except Exception as e:
            print(f"Error in get_village_recommendations: {e}")
            return {"error": str(e)}

    async def get_recommendation_detail(self, village_id: str, recommendation_title: str):
        """
        Get structured dashboard content and blog for a specific recommendation
        """
        try:
            # 1. Get village context
            context = await spatial_service.get_village_spatial_context(village_id)
            if "error" in context:
                return context

            village = context['village']
            
            # 2. Prepare risk context
            risk_status = "MODERATE"
            try:
                district = village.get("district", "Krishna")
                district_risks = await self.assess_district_risk(district)
                if district_risks:
                    v_risk = next((r for r in district_risks if r.get("id") == village_id), None)
                    if v_risk:
                        risk_status = v_risk.get("status", "MODERATE")
            except:
                pass

            ai_context = {
                **context,
                "risk_context": {
                    "status": risk_status,
                    "rainfall": village.get('average_rainfall_mm') or 850.0
                }
            }

            # 3. Get the specific recommendation technical details
            # We fetch all recommendations and find the one with the matching title
            all_recs = await self.get_village_recommendations(village_id)
            target_rec = None
            if isinstance(all_recs, dict) and "recommendations" in all_recs:
                target_rec = next((r for r in all_recs["recommendations"] if r.get("title") == recommendation_title), None)
            
            if not target_rec:
                target_rec = {"title": recommendation_title, "description": "Analyzing intervention details..."}

            # 4. Generate structured dashboard and blog post
            # We run these in parallel for performance
            import asyncio
            
            # Generate dynamic image prompt
            image_prompt = f"{target_rec.get('title')}, {village.get('name')} village, water conservation structure, photorealistic"
            
            structured_task = ai_service.generate_structured_recommendation(target_rec, ai_context)
            blog_task = ai_service.generate_recommendation_blog(target_rec, ai_context)
            image_task = ai_service.generate_image_from_text(image_prompt)
            
            structured_data, blog_content, generated_image_url = await asyncio.gather(structured_task, blog_task, image_task)

            return {
                "village_id": village_id,
                "title": recommendation_title,
                "content": structured_data,
                "blog": blog_content,
                "type": target_rec.get("type", "INTERVENTION"),
                "impact": target_rec.get("impact", "MEDIUM"),
                "hero": {
                    "image": generated_image_url,
                    "caption": f"Visualisation of {recommendation_title} in {village['name']}."
                }
            }
        except Exception as e:
            print(f"Error in get_recommendation_detail: {e}")
            # Robust fallback for frontend safety
            return {
                "village_id": village_id,
                "title": recommendation_title,
                "content": {
                    "overview": "Detailed technical specifications are currently being processed. Please refresh in a moment.",
                    "background": "Analysis of local soil and terrain profile.",
                    "technicalSpecifications": {"status": "Processing"},
                    "implementation": {"phases": []},
                    "expectedOutcomes": {"primary": ["Awaiting AI generation"]},
                    "costBreakdown": {"total": "Variable"},
                    "riskMitigation": ["Standard monitoring required"]
                },
                "blog": f"# {recommendation_title}\n\nOur AI is currently generating the detailed implementation guide for this intervention. This typically takes 30-45 seconds.",
                "type": "INTERVENTION",
                "impact": "MEDIUM",
                "hero": {
                    "image": "https://images.unsplash.com/photo-1540324155974-7523202daa3f?auto=format&fit=crop&q=80&w=1200",
                    "caption": "Awaiting visualization."
                },
                "error": str(e)
            }

drought_service = DroughtService()
