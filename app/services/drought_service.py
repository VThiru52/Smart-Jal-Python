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
        # In-memory cache for recommendations to avoid regenerating images
        self._recommendations_cache = {}

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

    async def get_village_recommendations(self, village_id: str, force_refresh: bool = False):
        """
        AI-driven intervention recommendations based on local characteristics using Gemini
        Uses Database persistence (Supabase) + In-memory caching to avoid regenerating images.
        """
        # 1. Check in-memory cache first for speed
        if not force_refresh and village_id in self._recommendations_cache:
            return self._recommendations_cache[village_id]
        
        # 2. Check Database persistence
        if not force_refresh:
            try:
                print(f"Checking DB cache for village: {village_id}")
                db_res = self.supabase.table("villages").select("recommendations_cache").eq("id", village_id).execute()
                if db_res.data and db_res.data[0].get("recommendations_cache"):
                    print(f"✅ Found DB cache for village: {village_id}")
                    cached_data = db_res.data[0]["recommendations_cache"]
                    # Update in-memory cache and return
                    self._recommendations_cache[village_id] = cached_data
                    return cached_data
                else:
                    print(f"ℹ️ No DB cache found for village: {village_id}")
            except Exception as e:
                print(f"❌ Database cache read error: {e}")

        try:
            # Get spatial context (soil, elevation)
            context = await spatial_service.get_village_spatial_context(village_id)
            if "error" in context:
                return context

            village = context['village']
            soil = context.get('soil', {})
            elevation = context.get('elevation', {})
            
            # Prepare context for AI
            risk_status = "MODERATE"
            try:
                district = village.get("district", "Krishna")
                normalized_district = district.capitalize()
                district_risks = await self.assess_district_risk(normalized_district)
                
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
            # 5. Generate recommendations
            recommendations_data = await ai_service.generate_water_recommendations(ai_context)
            
            # 6. Generate images for each recommendation in parallel
            if isinstance(recommendations_data, list):
                import asyncio
                
                async def attach_image(rec):
                    image_prompt = f"{rec.get('title')}, {village.get('name')} village, water conservation structure, photorealistic"
                    rec['image'] = await ai_service.generate_image_from_text(image_prompt)
                    return rec

                recommendations = await asyncio.gather(*[attach_image(rec) for rec in recommendations_data])
            else:
                recommendations = recommendations_data

            result = {
                "village_id": village_id,
                "village_name": village['name'],
                "risk_context": ai_context['risk_context'],
                "recommendations": recommendations,
                "generated_at": pd.Timestamp.now().isoformat()
            }
            
            # 7. Update caches (In-memory + Database)
            self._recommendations_cache[village_id] = result
            try:
                print(f"Storing recommendations in DB for village: {village_id}")
                update_res = self.supabase.table("villages").update({
                    "recommendations_cache": result
                }).eq("id", village_id).execute()
                print(f"✅ DB Update response: {update_res.data}")
            except Exception as e:
                print(f"❌ Database cache write error: {e}")
                
            return result
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
            # CRITICAL: Check caches first to avoid regenerating all 3 images
            target_rec = None
            
            # A. Check in-memory cache (fastest)
            if village_id in self._recommendations_cache:
                cached_data = self._recommendations_cache[village_id]
                if isinstance(cached_data, dict) and "recommendations" in cached_data:
                    target_rec = next((r for r in cached_data["recommendations"] if r.get("title") == recommendation_title), None)

            # B. Check Database persistence if not in memory
            if not target_rec:
                try:
                    db_res = self.supabase.table("villages").select("recommendations_cache").eq("id", village_id).execute()
                    if db_res.data and db_res.data[0].get("recommendations_cache"):
                        cached_data = db_res.data[0]["recommendations_cache"]
                        # Populate in-memory cache for next time
                        self._recommendations_cache[village_id] = cached_data
                        
                        if isinstance(cached_data, dict) and "recommendations" in cached_data:
                            target_rec = next((r for r in cached_data["recommendations"] if r.get("title") == recommendation_title), None)
                except Exception as e:
                    print(f"Database cache read error in detail: {e}")

            # C. Fallback: Create minimal one for AI generation
            if not target_rec:
                target_rec = {
                    "title": recommendation_title,
                    "description": f"Water conservation intervention: {recommendation_title}"
                }

            # 4. Generate structured dashboard and blog post
            # We run these in parallel for performance
            import asyncio
            
            structured_task = ai_service.generate_structured_recommendation(target_rec, ai_context)
            blog_task = ai_service.generate_recommendation_blog(target_rec, ai_context)
            
            # IMPORTANT: Reuse existing image from evaluation to avoid wasting API credits
            # Only generate a new image if one doesn't exist (e.g., fallback case)
            if target_rec and target_rec.get('image'):
                # Image already exists from evaluation - reuse it!
                generated_image_url = target_rec['image']
                structured_data, blog_content = await asyncio.gather(structured_task, blog_task)
            else:
                # No cached image found, generate a new one
                image_prompt = f"{target_rec.get('title')}, {village.get('name')} village, water conservation structure, photorealistic"
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
