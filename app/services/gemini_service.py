from google import genai
from app.core.config import settings
import logging
import json
import os
import uuid
import requests
import base64
import io
from typing import Dict, Any, List

class GeminiService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        if self.api_key:
            # Using the newer google-genai SDK with v1beta version for Imagen support
            self.client = genai.Client(api_key=self.api_key, http_options={'api_version': 'v1beta'})
        else:
            logging.warning("GEMINI_API_KEY not found. AI features will use mock responses.")
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
        
        Output MUST be valid JSON with ONLY the following keys:
        - recommendation: str
        - reason: str
        - cost_estimate: str
        - time_frame: str
        - success_probability: str
        - precautions: List[str]
        """
        
        try:
            response = self.client.models.generate_content(
                model='gemini-1.5-flash',
                contents=prompt,
                config={
                    'response_mime_type': 'application/json',
                }
            )
            if response and response.text:
                return json.loads(response.text)
            return self._mock_recommendation(village_data)
        except Exception as e:
            logging.error(f"Gemini API error (recommendation): {e}")
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
            response = self.client.models.generate_content(
                model='gemini-1.5-flash',
                contents=prompt,
                config={
                    'response_mime_type': 'application/json',
                }
            )
            if response and response.text:
                return json.loads(response.text)
            return {"error": "Failed to analyze land type"}
        except Exception as e:
            logging.error(f"Gemini API error (land_type): {e}")
            return {"error": "Failed to analyze land type"}

    async def generate_image_from_text(self, prompt: str) -> str:
        """
        Generates an image using Gemini's Imagen 3 model and saves it locally.
        Returns the local URL for the image.
        """
        if not self.api_key:
            logging.warning("GEMINI_API_KEY not found for image generation. Using fallback.")
            return self._get_pollination_fallback(prompt)

        try:
            # Using imagen-4.0-fast-generate-001 for higher quota limits (10/day Fast tier)
            response = self.client.models.generate_image(
                model='imagen-4.0-fast-generate-001',
                prompt=f"realistic, high quality, 4k, drone view, water management, {prompt}",
                config={
                    'number_of_images': 1,
                }
            )
            
            if response and response.generated_images:
                # Convert PIL Image or bytes to Base64
                img_data = response.generated_images[0].image
                
                # Robust conversion
                try:
                    buffered = io.BytesIO()
                    # Some SDK versions or environments might return bytes instead of PIL Image
                    if isinstance(img_data, bytes):
                        buffered.write(img_data)
                    else:
                        # Assume it's a PIL Image or something with .save()
                        # Use positional format for better compatibility
                        img_data.save(buffered, "PNG")
                    
                    img_str = base64.b64encode(buffered.getvalue()).decode()
                    return f"data:image/png;base64,{img_str}"
                except Exception as save_err:
                    logging.error(f"Error converting Gemini image to Base64: {save_err}")
                    logging.info(f"Image object type: {type(img_data)}")
                    # Fallback to pollinations if conversion fails
                    return self._get_pollination_fallback(prompt)
                
            logging.warning("No images found in Gemini response. Using Pollinations fallback.")
            return self._get_pollination_fallback(prompt)
            
        except Exception as e:
            # Check for quota exhaustion (429) or other API errors
            error_msg = str(e)
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                logging.warning(f"Gemini Image Quota Exceeded (Limit 70/day). Switching to Hugging Face fallback.")
            else:
                logging.error(f"Gemini Image API error: {e}")
            
            # Try Hugging Face first as requested by user
            hf_image = self._generate_huggingface_image(prompt)
            if hf_image:
                return hf_image
                
            return self._get_pollination_fallback(prompt)

    def _generate_huggingface_image(self, prompt: str) -> str:
        """
        Generates image using Hugging Face Inference API (Stable Diffusion XL).
        Saves locally and returns local URL.
        """
        api_key = settings.HUGGINGFACE_API_KEY
        if not api_key:
            return None
            
        API_URL = "https://router.huggingface.co/hf-inference/models/stabilityai/stable-diffusion-xl-base-1.0"
        headers = {"Authorization": f"Bearer {api_key}"}
        
        enhanced_prompt = f"realistic, high quality, 4k, drone view, water management, {prompt}, rural india context"

        try:
            logging.info(f"Attempting Hugging Face generation for: {prompt}")
            response = requests.post(API_URL, headers=headers, json={"inputs": enhanced_prompt}, timeout=30)
            
            if response.status_code == 200:
                # Convert response content to Base64
                img_str = base64.b64encode(response.content).decode()
                return f"data:image/png;base64,{img_str}"
            else:
                logging.warning(f"Hugging Face API failed: {response.text}")
                return None
        except Exception as e:
            logging.error(f"Hugging Face execution error: {e}")
            return None

    def _get_pollination_fallback(self, prompt: str) -> str:
        """
        Generates a high-quality alternative image URL using Pollinations.ai.
        """
        import urllib.parse
        import random
        
        # Enhanced prompt engineering for Pollinations/Stable Diffusion
        enhanced_prompt = f"cinematic drone shot of {prompt}, rural india village context, water conservation structure, 8k resolution, highly detailed, photorealistic, golden hour lighting, lush greenery"
        encoded_prompt = urllib.parse.quote(enhanced_prompt)
        seed = random.randint(1, 100000)
        
        # Using a fixed seed for consistent variety but better quality control could be added
        return f"https://image.pollinations.ai/prompt/{encoded_prompt}?seed={seed}&width=1280&height=720&nologo=true&model=flux"

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
