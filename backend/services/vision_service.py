import os
import base64
from typing import Optional
from PIL import Image
import io
import json
import google.generativeai as genai
from utils.logger import logger

class VisionService:
    """Service for analyzing medical images using Google Gemini Vision.
    
    Optimized: Single API call does both image analysis AND health response,
    eliminating the second LLM call entirely.
    """
    
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
        self.model_name = os.getenv("VISION_MODEL", "gemini-2.0-flash-lite")
        
        # Cache the model with generation config for JSON output
        self._model = None
        self._analysis_model = None
        if self.api_key:
            self._analysis_model = genai.GenerativeModel(
                self.model_name,
                system_instruction="""You are a medical AI assistant. Analyze the provided medical/health image and return a complete JSON response.
Return ONLY valid JSON in this exact format:
{"explanation":"detailed analysis of what you see in the image, describe all visible symptoms and findings completely","possible_conditions":[{"name":"condition name","likelihood":"possible","description":"brief description of the condition"}],"precautions":["actionable health tip"],"disclaimer":"This is for educational purposes only. Always consult a healthcare professional for proper diagnosis."}
IMPORTANT: You must complete ALL fields fully. Never leave any field incomplete or truncated. Provide a thorough explanation.""",
                generation_config={
                    "temperature": 0.3,
                    "top_p": 0.8,
                    "max_output_tokens": 2048,
                    "response_mime_type": "application/json",
                }
            )
            # Simple analysis model (no JSON, for fallback)
            self._model = genai.GenerativeModel(self.model_name)
            logger.info(f"Vision model cached: {self.model_name}")
    
    async def analyze_image_full(self, image_bytes: bytes, user_context: Optional[str] = None) -> dict:
        """Analyze image and return full health response in ONE API call.
        
        This replaces the old two-step flow (vision_service -> llm_service).
        """
        try:
            if not self._analysis_model:
                return {
                    "explanation": "Error: Vision service not configured (missing API Key).",
                    "possible_conditions": [],
                    "precautions": ["Please configure the API key."],
                    "disclaimer": "Service unavailable."
                }

            logger.info("Analyzing image with Gemini Vision (single-call)...")
            
            image = Image.open(io.BytesIO(image_bytes))
            
            prompt = "Analyze this medical/health image. Note visible symptoms, possible conditions, and recommended precautions."
            if user_context:
                prompt += f"\nUser context: {user_context}"
            
            response = await self._analysis_model.generate_content_async([prompt, image])
            
            raw = response.text if response else ""
            logger.info("Image analysis completed (single-call)")
            
            # Parse JSON response
            try:
                return json.loads(raw)
            except Exception:
                pass
            
            # Try cleaning markdown fences
            try:
                cleaned = raw.replace("```json", "").replace("```", "").strip()
                return json.loads(cleaned)
            except Exception:
                pass
            
            # Fallback: wrap raw text
            return {
                "explanation": raw or "Unable to analyze image. Please try again.",
                "possible_conditions": [],
                "precautions": ["Consult a healthcare professional for proper diagnosis."],
                "disclaimer": "For educational purposes only."
            }
        
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            return {
                "explanation": f"Unable to analyze image: {str(e)}",
                "possible_conditions": [],
                "precautions": ["Please try again or consult a healthcare professional."],
                "disclaimer": "Service error."
            }
    
    async def analyze_image(self, image_bytes: bytes, user_context: Optional[str] = None) -> str:
        """Legacy method - simple text analysis of image."""
        try:
            if not self._model:
                return "Error: Vision service not configured (missing API Key)."

            logger.info("Analyzing image with Gemini Vision...")
            image = Image.open(io.BytesIO(image_bytes))
            
            prompt = "Briefly analyze this medical/health image. Note visible symptoms or concerns. Keep it concise. Educational only."
            if user_context:
                prompt += f"\nContext: {user_context}"
            
            response = await self._model.generate_content_async([prompt, image])
            logger.info("Image analysis completed")
            return response.text
        
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            return f"Unable to analyze image: {str(e)}"

# Create singleton instance
vision_service = VisionService()
