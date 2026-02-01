from app.core.supabase import get_supabase_admin
from typing import List, Dict
import pandas as pd
from app.services.audit_service import audit_service
from app.services.ai_service import ai_service
import asyncio

class RechargeService:
    def __init__(self):
        self.supabase = get_supabase_admin()

    async def calculate_recharge_priorities(self, district: str = "Krishna"):
        try:
            # 1. Selection Logic Database: Pros and Cons
            STRUCTURE_KNOWLEDGE = {
                "Check Dam": {
                    "pros": "Highly effective for rapid runoff control; increases water retention in sloped terrains.",
                    "cons": "Site-specific construction needed; requires regular silt removal maintenance."
                },
                "Percolation Tank": {
                    "pros": "Excellent for large-scale groundwater enrichment; cost-effective for community use.",
                    "cons": "Requires significant land area; subject to evaporation losses in peak summer."
                },
                "Farm Pond": {
                    "pros": "Ideal for clayey soils; provides emergency irrigation buffer for farmers.",
                    "cons": "Captures only surface runoff; limited direct deep-aquifer recharge."
                },
                "Recharge Pit": {
                    "pros": "Minimal land footprint; can be implemented at household or farm levels.",
                    "cons": "Filters require frequent cleaning to prevent clogging; low volumetric capacity."
                },
                "Injection Well": {
                    "pros": "Bypasses impermeable layers to recharge deep aquifers directly.",
                    "cons": "High initial cost; risk of groundwater contamination if not properly filtered."
                },
                "Contour Trenching": {
                    "pros": "Prevents soil erosion on slopes while facilitating localized infiltration.",
                    "cons": "Manual labor intensive; only suitable for specific topographic gradients."
                },
                "Sunken Tank": {
                    "pros": "Utilizes natural depressions; minimal structural engineering required.",
                    "cons": "Susceptible to algae growth; water quality may degrade without circulation."
                }
            }

            # 2. Fetch Village data
            print(f"📡 Fetching villages for district: {district}")
            villages_resp = self.supabase.table("villages").select(
                "id, name, population, land_area_ha, soil_type, elevation_m" 
            ).eq("district", district).execute()
            
            if not villages_resp.data:
                return []
                
            df_villages = pd.DataFrame(villages_resp.data)

            # 3. Fetch Latest Water levels
            readings_resp = self.supabase.rpc("get_village_avg_water_levels", {}).execute()
            reading_map = {r['village_id']: r['avg_level_mbgl'] for r in readings_resp.data} if readings_resp.data else {}
            
            recommendations = []
            for _, village in df_villages.iterrows():
                v_id = village['id']
                avg_depth = reading_map.get(v_id, 10.0)
                soil_type = str(village.get('soil_type', '') or '').lower()
                elevation = float(village.get('elevation_m') or 0)
                
                # --- Advanced Priority Score (0-10) ---
                depth_factor = min(avg_depth / 40.0, 1.0)
                soil_score = 1.0 if 'sand' in soil_type else (0.8 if 'loam' in soil_type else 0.4)
                elev_factor = 1.0 if elevation < 50 else (0.6 if elevation < 150 else 0.2)
                
                priority_score = min(((depth_factor * 0.5) + (soil_score * 0.3) + (elev_factor * 0.2)) * 10, 10.0)

                # --- NEW Triple-Suggestion Engine ---
                def get_suggestions():
                    suggestions = []
                    
                    # 1. Primary (Soil + Terrain Fit)
                    # Data analysis showed max elevation is 45m, so thresholds need to be lower
                    if elevation > 35:
                        primary = "Check Dam" if 'sand' in soil_type or 'alluvial' in soil_type else "Contour Trenching"
                    elif 'clay' in soil_type or 'black cotton' in soil_type:
                        primary = "Farm Pond"
                    elif 'red loyamy' in soil_type or 'loam' in soil_type:
                        primary = "Percolation Tank"
                    elif 'sand' in soil_type:
                        primary = "Recharge Pit"
                    else:
                        primary = "Percolation Tank" # Default
                    suggestions.append(primary)

                    # 2. Secondary (Utility Fit based on Depth + Soil)
                    if avg_depth > 30:
                        secondary = "Injection Well"
                    elif ('sand' in soil_type or 'alluvial' in soil_type) and elevation < 25:
                        secondary = "Percolation Tank" if primary != "Percolation Tank" else "Recharge Pit"
                    elif 'clay' in soil_type or 'black cotton' in soil_type:
                        secondary = "Sunken Tank"
                    else:
                        secondary = "Recharge Pit"
                    
                    if secondary in suggestions: 
                        # Diversity logic
                        if "Injection Well" not in suggestions and avg_depth > 15:
                            secondary = "Injection Well"
                        elif "Recharge Pit" not in suggestions:
                            secondary = "Recharge Pit"
                        else:
                            secondary = "Sunken Tank"
                    suggestions.append(secondary)

                    # 3. Alternative (General Fit + Diversity)
                    fallback_options = ["Sunken Tank", "Recharge Pit", "Percolation Tank", "Injection Well", "Contour Trenching", "Check Dam", "Farm Pond"]
                    
                    # Try to pick something not already selected
                    alternative = None
                    for opt in fallback_options:
                        if opt not in suggestions:
                            # Add some logic-based preference for the 3rd spot
                            if opt == "Injection Well" and avg_depth < 10: continue
                            if opt == "Check Dam" and elevation < 20: continue
                            alternative = opt
                            break
                    
                    if not alternative:
                        alternative = "Recharge Pit" if "Recharge Pit" not in suggestions else "Sunken Tank"
                    
                    suggestions.append(alternative)
                    
                    return suggestions[:3]

                suggestion_names = get_suggestions()
                
                # Build rich objects with Pros/Cons
                suggestions_data = []
                for name in suggestion_names:
                    knowledge = STRUCTURE_KNOWLEDGE.get(name, {"pros": "General recharge", "cons": "Maintenance"})
                    suggestions_data.append({
                        "name": name,
                        "advantages": knowledge["pros"],
                        "disadvantages": knowledge["cons"]
                    })

                recommendations.append({
                    "village_id": v_id,
                    "village_name": village['name'],
                    "priority_score": round(float(priority_score), 2),
                    "avg_depth_mbgl": round(float(avg_depth), 2),
                    "soil_type": village.get('soil_type') or "Unknown",
                    "elevation": elevation,
                    "mandal": village.get('mandal', 'Unknown'),
                    "district": district,
                    "suggestions": suggestions_data,
                    "is_ai_generated": False,
                    "suitability_rank": 1 if priority_score > 7 else (2 if priority_score > 4 else 3)
                })

            # Sort by priority
            recommendations = sorted(recommendations, key=lambda x: x['priority_score'], reverse=True)

            # --- DYNAMIC AI ENHANCEMENT FOR TOP 5 ---
            top_5 = recommendations[:5]
            
            async def enhance_with_ai(rec):
                try:
                    context = {
                        "village": {"name": rec["village_name"], "mandal": rec.get("mandal"), "district": rec.get("district")},
                        "soil": {"soil_name": rec["soil_type"]},
                        "elevation": {"elevation_m": rec["elevation"]},
                        "risk_context": {"status": "CRITICAL" if rec["priority_score"] >= 7 else "MODERATE", "rainfall": 850}
                    }
                    
                    ai_recs = await ai_service.generate_water_recommendations(context)
                    if ai_recs and len(ai_recs) >= 3:
                        formatted_suggestions = []
                        for s in ai_recs[:3]:
                            formatted_suggestions.append({
                                "name": s.get("title", "Recharge Structure"),
                                "advantages": s.get("description", "Scientific recharge implementation."),
                                "disadvantages": f"Requires {s.get('impact', 'standard')} level maintenance and monitoring."
                            })
                        rec["suggestions"] = formatted_suggestions
                        rec["is_ai_generated"] = True
                except Exception as ai_err:
                    print(f"⚠️ AI Enhancement failed for {rec['village_name']}: {ai_err}")
                return rec

            if top_5:
                loop = asyncio.get_event_loop()
                tasks = [enhance_with_ai(rec) for rec in top_5]
                # Note: enhance_with_ai is async but calls a blocking method inside AIService.
                # However, AIService's generate_water_recommendations is also async and mistakenly 
                # calls a sync client. I'll wrap the AIService call in run_in_executor inside enhance_with_ai.
                
                async def enhanced_ai_wrapper(rec):
                    try:
                        context = {
                            "village": {"name": rec["village_name"], "mandal": rec.get("mandal"), "district": rec.get("district")},
                            "soil": {"soil_name": rec["soil_type"]},
                            "elevation": {"elevation_m": rec["elevation"]},
                            "risk_context": {"status": "CRITICAL" if rec["priority_score"] >= 7 else "MODERATE", "rainfall": 850}
                        }
                        # Run the blocking AI call in a thread pool
                        ai_recs = await loop.run_in_executor(None, lambda: asyncio.run(ai_service.generate_water_recommendations(context)))
                        if ai_recs and len(ai_recs) >= 3:
                            formatted_suggestions = []
                            for s in ai_recs[:3]:
                                formatted_suggestions.append({
                                    "name": s.get("title", "Recharge Structure"),
                                    "advantages": s.get("description", "Scientific recharge implementation."),
                                    "disadvantages": f"Requires {s.get('impact', 'standard')} level maintenance and monitoring."
                                })
                            rec["suggestions"] = formatted_suggestions
                            rec["is_ai_generated"] = True
                    except Exception as ai_err:
                        print(f"⚠️ AI Enhancement failed for {rec['village_name']}: {ai_err}")
                    return rec

                tasks = [enhanced_ai_wrapper(rec) for rec in top_5]
                enhanced_top_5 = await asyncio.gather(*tasks)
                # Replace the original top 5 with enhanced ones
                recommendations[:5] = enhanced_top_5
            
            return recommendations
        except Exception as e:
            print(f"❌ Error in calculate_recharge_priorities: {e}")
            return []
        except Exception as e:
            print(f"❌ Error in calculate_recharge_priorities: {e}")
            # If we calculated recommendations but failed later, return them if possible
            if 'recommendations' in locals() and recommendations:
                 return recommendations
            return []

recharge_service = RechargeService()
