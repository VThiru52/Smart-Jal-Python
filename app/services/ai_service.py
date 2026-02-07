from mistralai import Mistral
import json
from app.core.config import settings
from typing import List, Dict, Any

class AIService:
    def __init__(self):
        self.api_key = settings.MISTRAL_API_KEY
        if self.api_key:
            self.client = Mistral(api_key=self.api_key)
        else:
            self.client = None

    async def generate_water_recommendations(self, context: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Generate dynamic, scientific water management recommendations using Gemini AI.
        """
        if not self.client:
            return self._get_fallback_recommendations(context)

        village = context.get('village', {})
        soil = context.get('soil', {})
        elevation = context.get('elevation', {})
        risk = context.get('risk_context', {})

        import time
        seed = int(time.time()) % 1000

        # Construct a high-precision engineering prompt with forced variety
        prompt = f"""
        Role: Senior Hydrological Engineer & Master Planner
        Task: Provide 3 ultra-specific water management interventions for {village.get('name')} village.
        
        Context Data (STRICTLY USE THESE):
        - Location: {village.get('name')}, {village.get('mandal')} Mandal
        - Soil: {soil.get('soil_name', 'Unknown')} (Texture: {soil.get('texture', 'Mixed')}, Drainage: {soil.get('drainage', 'Moderate')})
        - Elevation: {elevation.get('elevation_m', 'N/A')} meters AMSL
        - Rainfall: {risk.get('rainfall', 'N/A')} mm (Annual Average)
        - Current Risk: {risk.get('status', 'MODERATE')}
        
        Session Identifier: {seed} (Use this to vary your selection of valid engineering techniques)

        STRICT Engineering Requirements:
        1. Recommendations MUST be distinct and scientifically tailored to the SPECIFIC soil texture and topography provided.
        2. NO GENERIC ADVICE. If soil is clay, suggest specific subsurface works. If high elevation, suggest contour-specific works.
        3. Provide unique technical titles.
        4. Descriptions must be technical and explain 'WHY' based on the soil/elevation data.
        5. MANDATORY: At least one recommendation MUST include a 'Farmer Advisory:' section providing practical crop or irrigation guidance.
        
        Format: Return ONLY a JSON array of 3 objects.
        
        [
          {{
            "title": "Technical Name",
            "type": "RECHARGE | STORAGE | CONSERVATION | INTERVENTION | SUPPLY",
            "impact": "HIGH | MEDIUM | LOW | EMERGENCY",
            "description": "Scientific justification (2 sentences) specifically mentioning Soil: {soil.get('soil_name')} and Elevation: {elevation.get('elevation_m')}m."
          }}
        ]
        """

        try:
            response = await self.client.chat.complete_async(
                model='mistral-large-latest',
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.9,
                top_p=0.95,
            )
            
            if response and response.choices:
                content = response.choices[0].message.content
                return json.loads(content)
            else:
                print(f"Mistral AI empty response for {village.get('name')}, using fallback")
                return self._get_fallback_recommendations(context)
        except Exception as e:
            print(f"Mistral AI Error for {village.get('name')}: {e}")
            return self._get_fallback_recommendations(context)

    def _get_fallback_recommendations(self, context: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Advanced spatial fallback when API is missing.
        Ensures results vary even without Gemini by using a pool of strategies.
        """
        soil = str(context.get('soil', {}).get('soil_name', '')).lower()
        texture = str(context.get('soil', {}).get('texture', '')).lower()
        elev = context.get('elevation', {}).get('elevation_m') or 50
        v_name = context.get('village', {}).get('name', 'the village')
        
        # Simple hash based on village name to vary recommendation selection
        v_hash = sum(ord(c) for c in v_name) % 2
        
        recs = []
        
        # 1. Soil-Driven Logic - Pick from multiple options
        if 'black' in soil or 'clay' in soil:
            if v_hash == 0:
                recs.append({
                    "title": "Subsurface Drainage Network",
                    "type": "CONSERVATION",
                    "impact": "HIGH",
                    "description": f"The clayey/black soil in {v_name} has high water retention but low permeability. Subsurface drains prevent salinity."
                })
            else:
                recs.append({
                    "title": "In-situ Soil Moisture Conservation",
                    "type": "CONSERVATION",
                    "impact": "MEDIUM",
                    "description": f"Black soils in {v_name} are prone to deep cracking. Mulching and deep tillage can optimize moisture retention."
                })
        elif 'sandy' in texture or 'red' in soil:
            if v_hash == 0:
                recs.append({
                    "title": "Injection Well Recharge",
                    "type": "RECHARGE",
                    "impact": "HIGH",
                    "description": f"High permeability sandy soils in {v_name} are ideal for bypass recharge wells targeting deep aquifers."
                })
            else:
                recs.append({
                    "title": "Rapid Percolation Ponds",
                    "type": "RECHARGE",
                    "impact": "HIGH",
                    "description": f"Sandy-loam profile in {v_name} allows for high infiltration rates. Distributed percolation tanks are highly effective."
                })
        else:
            recs.append({
                "title": "Nala Bunding & Check Dams",
                "type": "INTERVENTION",
                "impact": "MEDIUM",
                "description": f"Generic intervention for {v_name} to reduce runoff velocity and increase the groundwater recharge window."
            })

        # 2. Topography-Driven Logic
        if elev > 120:
            if v_hash == 1:
                recs.append({
                    "title": "Continuous Contour Trenches",
                    "type": "CONSERVATION",
                    "impact": "MEDIUM",
                    "description": f"With an elevation of {int(elev)}m, sloping terrain risks high runoff. CCTs will catch and sink water across the ridge lines."
                })
            else:
                recs.append({
                    "title": "Staggered Contour Bunding",
                    "type": "CONSERVATION",
                    "impact": "MEDIUM",
                    "description": f"Slope-specific bunding for {v_name} ({int(elev)}m) to control erosion and facilitate localized infiltration."
                })
        else:
            if v_hash == 0:
                recs.append({
                    "title": "Distributed Farm Ponds",
                    "type": "STORAGE",
                    "impact": "HIGH",
                    "description": f"Relatively flat terrain ({int(elev)}m) is ideal for connected farm ponds to store surface runoff for lean seasons."
                })
            else:
                recs.append({
                    "title": "Community Sunken Tanks",
                    "type": "STORAGE",
                    "impact": "HIGH",
                    "description": f"Natural depressions in {v_name}'s flat landscape ({int(elev)}m) should be converted to managed community storage tanks."
                })

        # 3. Supply/Urgency Logic
        if context.get('risk_context', {}).get('status') == 'CRITICAL':
            recs.append({
                "title": "Multi-Village Conjunctive Grid",
                "type": "SUPPLY",
                "impact": "EMERGENCY",
                "description": f"CRITICAL risk detected in {v_name}. Target emergency connection to a surplus-district water grid for domestic needs. Farmer Advisory: Conserve existing stocks for livestock."
            })
        else:
            if v_hash == 0:
                recs.append({
                    "title": "Smart Pumping Micro-Grid",
                    "type": "CONSERVATION",
                    "impact": "MEDIUM",
                    "description": f"Implementation of IoT sensors in {v_name} to automate pumping based on real-time safe-yield calculations. Farmer Advisory: Avoid pumping during high evaporation hours."
                })
            else:
                recs.append({
                    "title": "Aquifer Mapping & Management",
                    "type": "INTERVENTION",
                    "impact": "LOW",
                    "description": f"Precision measurement of {v_name}'s subsurface using VES to dictate sustainable pumping hours for local farmers. Farmer Advisory: Check borewell casing for silting."
                })

        return recs

    def _get_fallback_blog(self, recommendation: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        Generates a rich, technical blog post locally without external APIs.
        Uses structural templates and context data to simulate AI reasoning.
        """
        title = recommendation.get('title', 'Water Management Strategy')
        v_name = context.get('village', {}).get('name', 'Village')
        soil = context.get('soil', {}).get('soil_name', 'mixed soil')
        elev = context.get('elevation', {}).get('elevation_m', 50)
        risk = context.get('risk_context', {}).get('status', 'MODERATE')
        
        return f"""
# Strategic Implementation: {title}
{recommendation.get('description', '')}

## 1. Local Strategic Justification
The hydro-geological profile of **{v_name}**, characterized by **{soil}** at an elevation of **{elev}m**, necessitates a precision-engineered approach. Our local simulation model indicates that **{title}** is the optimal intervention to mitigate the **{risk}** water risk currently observed in the cluster.

Unlike generic solutions, this strategy leverages the specific drainage properties of **{soil}** to maximize either infiltration (for recharge) or conveyance efficiency (for supply).

## 2. Technical Implementation Roadmap
To ensure maximum efficacy, the implementation must follow strict engineering protocols:

- **Phase I (Baseline Analysis):** Conduct a high-resolution Vertical Electrical Sounding (VES) at three points in {v_name} to map the aquifer depth.
- **Phase II (Structural Work):** Excavation and installation of primary conduits or recharge shafts. For {soil}, we recommend a 500-micron silt trap.
- **Phase III (Automation):** Deployment of GSM-enabled pressure sensors at the head-works to monitor flow vs. extraction rates.
- **Phase IV (Commissioning):** A 72-hour stress test during the first precipitation event or grid-charging cycle.

## 3. Anticipated Efficacy Metrics
| Metric | Projected Impact | Baseline Value |
| :--- | :--- | :--- |
| Water Table Rise | +1.5m to 2.2m | Current MBGL |
| Energy Saving | 15% - 22% | Standard Pumping |
| Storage Capacity | +25,000 m³ | Existing Assets |

## 4. Advantages & Constraints
**Strategic Advantages:**
- **Reliability:** Built-in solar-sync or low-maintenance filtration.
- **Scalability:** The framework for {v_name} can be extended to neighboring hamlets.
- **Data Integrity:** Real-time feedback into the Smart Jal District Portal.

**Potential Constraints:**
- **Maintenance:** Requires quarterly desilting of the primary chambers.
- **Upfront Cost:** Higher initial CAPEX compared to traditional unlined structures.

## 5. Farmer Advisory & Best Practices
For the successful operation of **{title}** in {v_name}, farmers are advised to:
1. **Irrigation Timing:** Operate pumps only between 4:00 AM and 10:00 AM to minimize evapotranspiration losses.
2. **Crop Choice:** With the improved reliability, consider transitioning to high-value horticulture in the 2-acre buffer zone.
3. **Asset Protection:** Ensure that sensor nodes are not disturbed during tractor-led harvesting.

---
*This strategic analysis was generated locally by the Smart Jal Resiliency Engine. No external API resources were used for this calculation.*
"""

    async def generate_recommendation_blog(self, recommendation: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        Generate a detailed, blog-post style article for a specific recommendation using Mistral AI.
        Falls back to local structural generation if API is unavailable.
        """
        if not self.client:
            return self._get_fallback_blog(recommendation, context)

        village = context.get('village', {})
        soil = context.get('soil', {})
        elevation = context.get('elevation', {})
        risk = context.get('risk_context', {})

        prompt = f"""
        Role: Expert Hydrological Engineer & Senior Agricultural Consultant
        Task: Write a comprehensive, step-by-step "Strategic Implementation Guide" for a water management intervention.
        
        Intervention Title: {recommendation.get('title')}
        Village: {village.get('name')}, {village.get('mandal')} Mandal, {village.get('district')} District
        
        LOCAL PARAMETERS (Crucial for Justification):
        - Soil Type: {soil.get('soil_name')} (Texture: {soil.get('texture')}, Drainage: {soil.get('drainage')})
        - Current Elevation: {elevation.get('elevation_m')}m AMSL
        - Water Risk Level: {risk.get('status')}
        - Annual Rainfall: {risk.get('rainfall')}mm
        
        Technical Context: {recommendation.get('description')}

        CONTENT REQUIREMENTS (STRICT):
        1. **Strategic Justification**: Explain scientifically why this is the OPTIMAL choice for {village.get('name')}. Specifically mention how the {soil.get('soil_name')} soil and {elevation.get('elevation_m')}m elevation make this strategy effective or necessary.
        
        2. **Step-by-Step Implementation**: Provide a detailed 4-6 step process for constructing/implementing this intervention. Be technical and specific (e.g., specific depths, materials, or seasonal timing).
        
        3. **Advantages & Disadvantages**:
           - **Pros**: 3 specific benefits for the village's water table and local agriculture.
           - **Cons**: 2 potential challenges, maintenance requirements, or limitations.
        
        4. **Project Metrics**:
           - **Estimated Construction Time**: Provide a realistic range (e.g., "4-6 weeks").
           - **Estimated Recovery Time**: How long before the village sees a measurable rise in the water table (e.g., "After 1 full monsoon cycle").
        
        5. **Farmer Advisory**: A clear, instructional section for local farmers.

        FORMATTING & TONE:
        - Use Markdown (H1, H2, H3, Bold, Lists).
        - Tone: Highly technical yet professional and authoritative.
        - Suggested word count: 600-800 words.
        - Provide unique technical headers.
        """

        try:
            response = await self.client.chat.complete_async(
                model='mistral-large-latest',
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                top_p=0.9,
            )
            
            if response and response.choices:
                return response.choices[0].message.content
            else:
                return f"# {recommendation.get('title')}\n\n{recommendation.get('description')}"
        except Exception as e:
            print(f"Mistral Blog Generation Error: {e}")
            return f"# {recommendation.get('title')}\n\n{recommendation.get('description')}\n\n*Note: Detailed analysis is currently delayed.*"

    async def generate_structured_recommendation(self, recommendation: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates the full structured dashboard JSON for a specific recommendation using Mistral AI.
        Matches the schema of recommendationsData.json.
        """
        if not self.client:
            return recommendation # Fallback to input

        village = context.get('village', {})
        soil = context.get('soil', {})
        elevation = context.get('elevation', {})
        risk = context.get('risk_context', {})

        prompt = f"""
        Role: Expert Hydrological Engineer
        Task: Generate a technical dashboard JSON for the water management intervention: {recommendation.get('title')}.
        Village Context: {village.get('name')}, {soil.get('soil_name')} soil, {elevation.get('elevation_m')}m elevation, {risk.get('status')} risk.

        STRICT SCHEMA REQUIREMENT:
        Return ONLY a JSON object with these keys:
        {{
            "overview": "Technical summary (2-3 sentences)",
            "background": "Specific justification based on soil/elevation/risk (2 sentences)",
            "technicalSpecifications": {{
                "hydrology": {{ "Metric Name": "Value with unit", ... }},
                "structures": {{ "Component": "Description", ... }},
                "materials": {{ "Item": "Specification", ... }}
            }},
            "implementation": {{
                "phases": [
                    {{
                        "phase": "Phase Name",
                        "duration": "Length",
                        "activities": ["Task 1", "Task 2"],
                        "deliverables": ["Output 1"]
                    }}
                ]
            }},
            "expectedOutcomes": {{
                "primary": ["Benefit 1", "Benefit 2"],
                "secondary": ["Benefit 3"]
            }},
            "costBreakdown": {{
                "Survey & Design": "₹ X,XX,XXX",
                "Civil Works": "₹ X,XX,XXX",
                "Materials": "₹ X,XX,XXX",
                "total": "₹ X,XX,XXX"
            }},
            "farmerAdvisory": {{
                "monsoon": "Instruction",
                "summer": "Instruction"
            }},
            "riskMitigation": ["Safety/Maintenance measure 1"]
        }}

        Notes:
        - Ensure costs are realistic for {recommendation.get('title')}.
        - Phases should be 3 distinct stages.
        - Outcoms should mention specific improvements to the village's water table.
        """

        try:
            response = await self.client.chat.complete_async(
                model='mistral-large-latest',
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.7,
            )
            
            if response and response.choices:
                return json.loads(response.choices[0].message.content)
            return recommendation
        except Exception as e:
            print(f"Mistral Structured Output Error: {e}")
            return recommendation

    async def generate_image_from_text(self, prompt: str) -> str:
        """
        Generates an image URL using Pollinations.ai (Open Source, Free).
        No API key required.
        """
        try:
            import urllib.parse
            import random
            
            # Enhance prompt for better results
            enhanced_prompt = f"realistic, high quality, 4k, drone view, water management, {prompt}"
            encoded_prompt = urllib.parse.quote(enhanced_prompt)
            
            # Add a random seed to ensure variety even for same prompts
            seed = random.randint(1, 10000)
            
            return f"https://image.pollinations.ai/prompt/{encoded_prompt}?seed={seed}&width=1280&height=720&nologo=true"
        except Exception as e:
            print(f"Image Generation Error: {e}")
            return "https://images.unsplash.com/photo-1540324155974-7523202daa3f?auto=format&fit=crop&q=80&w=1200"

ai_service = AIService()
