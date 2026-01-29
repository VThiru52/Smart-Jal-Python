from mistralai import Mistral
from app.core.config import settings
import logging
import json
from typing import Dict, Any, List

class GeminiService:
    def __init__(self):
        self.api_key = settings.MISTRAL_API_KEY
        if self.api_key:
            self.client = Mistral(api_key=self.api_key)
        else:
            logging.warning("MISTRAL_API_KEY not found. AI features will use mock responses.")
            self.client = None

    async def generate_solution_recommendation(
        self, 
        village_data: Dict[str, Any], 
        deficit: float, 
        resources: List[str]
    ) -> Dict[str, Any]:
        """
        Generates a solution recommendation based on village data and water deficit.
        """
        if not self.client:
            return self._mock_recommendation(village_data)

        prompt = f"""
        Village Data: {json.dumps(village_data)}
        Problem: Water deficit of {deficit} million liters
        Available Resources: {", ".join(resources)}
        
        Recommend the BEST solution from:
        - Pipeline from nearby village (if water-rich village within 5km)
        - Dig new borewell (if aquifer depth < 30m)
        - Construct check dam (if gradient > 5%)
        - Build pond (if clay soil present)
        
        Output valid JSON with the following keys:
        - recommendation: str
        - reason: str
        - cost_estimate: str
        - time_frame: str
        - success_probability: str
        - precautions: List[str]
        """
        
        try:
            response = self.client.chat.complete(
                model='mistral-large-latest',
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            if response and response.choices:
                return json.loads(response.choices[0].message.content)
            return self._mock_recommendation(village_data)
        except Exception as e:
            logging.error(f"Mistral API error: {e}")
            return self._mock_recommendation(village_data)

    async def analyze_land_type(self, geo_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyzes land type and suggests precautions.
        """
        if not self.client:
            return {"analysis": "Mock Analysis: Clay soil detected.", "precautions": ["Avoid deep excavation"]}

        prompt = f"""
        Analyze the following geological data and provide soil percolation insights:
        {json.dumps(geo_data)}
        
        Return JSON with 'analysis' and 'precautions' keys.
        """
        try:
            response = self.client.chat.complete(
                model='mistral-large-latest',
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            if response and response.choices:
                return json.loads(response.choices[0].message.content)
            return {"error": "Failed to analyze land type"}
        except Exception as e:
            logging.error(f"Mistral API error: {e}")
            return {"error": "Failed to analyze land type"}

    def _mock_recommendation(self, village_data) -> Dict[str, Any]:
        return {
            "recommendation": "Construct Check Dam",
            "reason": "High gradient detected and seasonal stream availability.",
            "cost_estimate": "₹12,00,000 - ₹15,00,000",
            "time_frame": "4-6 weeks",
            "success_probability": "85%",
            "precautions": [
                "Conduct soil stability test",
                "Ensure downstream flow rights"
            ]
        }

gemini_service = GeminiService()
