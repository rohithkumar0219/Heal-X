import os
import json
import asyncio
import time
from typing import Dict, List, Optional
import google.generativeai as genai
from utils.logger import logger
from models.schemas import PossibleCondition

class LLMService:
    """Service for interacting with Google Gemini Models."""

    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            logger.error("GOOGLE_API_KEY not found in environment variables")
        else:
            genai.configure(api_key=self.api_key)
        
        self.model_name = os.getenv("LLM_MODEL", "gemini-2.0-flash-lite")
        
        self.system_prompt = """You are a medical AI assistant. Return ONLY valid JSON in this exact format:
{"explanation":"thorough health analysis","possible_conditions":[{"name":"condition name","likelihood":"possible","description":"brief description"}],"precautions":["actionable health tip"],"disclaimer":"This is for educational purposes only. Always consult a healthcare professional."}
IMPORTANT: Complete ALL fields fully. Never truncate any field. Provide a detailed explanation."""

        # Cache the model instance (don't recreate per request)
        self._model = None
        if self.api_key:
            self._model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=self.system_prompt,
                generation_config={
                    "temperature": 0.3,
                    "top_p": 0.8,
                    "max_output_tokens": 2048,
                    "response_mime_type": "application/json",
                }
            )
            logger.info(f"LLM model cached: {self.model_name}")

    def create_structured_prompt(self, user_query: Optional[str] = None, image_analysis: Optional[str] = None, voice_transcription: Optional[str] = None) -> str:
        parts = []
        if voice_transcription:
            parts.append(f"Voice Input: {voice_transcription}")
        if user_query:
            parts.append(f"Query: {user_query}")
        if image_analysis:
            parts.append(f"Image Analysis: {image_analysis}")
        
        if not parts:
            return "Provide a general health tip."
        
        return "\n".join(parts)

    async def generate_response(
        self, 
        user_query: Optional[str] = None,
        image_analysis: Optional[str] = None,
        voice_transcription: Optional[str] = None
    ) -> Dict:
        try:
            if not self._model:
                return self._fallback_response("Configuration Error: Google API Key is missing.")

            prompt_content = self.create_structured_prompt(user_query, image_analysis, voice_transcription)
            
            logger.info(f"Sending to Gemini ({self.model_name})...")

            # Retry with backoff for 429 errors
            max_retries = 2
            response = None
            for attempt in range(max_retries + 1):
                try:
                    response = await self._model.generate_content_async(prompt_content)
                    logger.info("Gemini response received")
                    break
                except Exception as api_err:
                    err_str = str(api_err)
                    if "429" in err_str and attempt < max_retries:
                        wait = 10  # Quick retry
                        logger.warning(f"Rate limited, retrying in {wait}s (attempt {attempt+1}/{max_retries})")
                        await asyncio.sleep(wait)
                    elif "429" in err_str:
                        logger.error("All retries exhausted for 429")
                        return self._fallback_response("Service is busy. Please try again in a moment.")
                    else:
                        raise api_err
            raw = response.text if response else ""
            
            # Try parsing as JSON
            try:
                result = json.loads(raw)
                return result
            except Exception:
                pass
            
            # Try cleaning markdown fences
            try:
                cleaned = raw.replace("```json", "").replace("```", "").strip()
                result = json.loads(cleaned)
                return result
            except Exception:
                pass
            
            # Final fallback: use raw text as explanation
            logger.warning("Could not parse JSON, using raw text")
            return {
                "explanation": raw or "Analysis complete. Please consult a healthcare professional for detailed advice.",
                "possible_conditions": [],
                "precautions": ["Consult a healthcare professional for proper diagnosis."],
                "disclaimer": "For educational purposes only."
            }

        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            return self._fallback_response(str(e))

    def _fallback_response(self, error_msg: str) -> Dict:
        logger.error(f"Fallback triggered: {error_msg}")
        return {
            "explanation": "I'm temporarily unable to process your request. Please try again in a moment.",
            "possible_conditions": [],
            "precautions": ["If you have urgent health concerns, please contact a healthcare professional directly."],
            "disclaimer": "Service temporarily unavailable."
        }

# Singleton instance
llm_service = LLMService()
