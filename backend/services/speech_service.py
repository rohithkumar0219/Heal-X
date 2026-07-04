import os
import asyncio
import time
from pathlib import Path
import google.generativeai as genai
from utils.logger import logger

class SpeechService:
    """Service for speech processing using Google Gemini.
    
    Optimized: Model instance is cached, file upload waits for ACTIVE state,
    and uses async generation.
    """
    
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
        self.model_name = os.getenv("WHISPER_MODEL", "gemini-2.0-flash-lite")
        
        # Cache the model instance
        self._model = None
        if self.api_key:
            self._model = genai.GenerativeModel(self.model_name)
            logger.info(f"Speech model cached: {self.model_name}")
    
    async def transcribe_audio(self, audio_path: Path) -> str:
        """Transcribe audio file to text.
        
        Uses Gemini's file upload API + cached model.
        Waits for file to reach ACTIVE state before processing.
        Returns empty string if transcription fails or audio has no speech.
        """
        try:
            if not self._model:
                logger.error("Speech model not initialized (missing API key)")
                return ""
            
            # Validate file exists and has content
            audio_path = Path(audio_path)
            if not audio_path.exists():
                logger.error(f"Audio file does not exist: {audio_path}")
                return ""
            
            file_size = audio_path.stat().st_size
            logger.info(f"Audio file: {audio_path} (size: {file_size} bytes, suffix: {audio_path.suffix})")
            
            if file_size < 100:  # Too small to contain real audio
                logger.error(f"Audio file too small ({file_size} bytes), likely empty recording")
                return ""
            
            loop = asyncio.get_event_loop()
            
            # Determine MIME type from extension
            mime_map = {
                '.webm': 'audio/webm',
                '.ogg': 'audio/ogg',
                '.mp4': 'audio/mp4',
                '.m4a': 'audio/mp4',
                '.mp3': 'audio/mpeg',
                '.wav': 'audio/wav',
            }
            mime_type = mime_map.get(audio_path.suffix.lower(), 'audio/webm')
            logger.info(f"Using MIME type: {mime_type}")
            
            # Upload file to Gemini File API with explicit MIME type
            logger.info(f"Uploading audio file to Gemini...")
            audio_file = await loop.run_in_executor(
                None, lambda: genai.upload_file(path=str(audio_path), mime_type=mime_type)
            )
            logger.info(f"Upload successful: {audio_file.name}")
            
            # Wait for file to become ACTIVE (critical for audio/video files)
            logger.info(f"Waiting for file to become active: {audio_file.name}")
            max_wait = 60  # increased from 30s
            start_time = time.time()
            
            while True:
                file_info = await loop.run_in_executor(
                    None, lambda: genai.get_file(audio_file.name)
                )
                
                state_name = file_info.state.name
                elapsed = time.time() - start_time
                logger.info(f"File state: {state_name} (elapsed: {elapsed:.1f}s)")
                
                if state_name == "ACTIVE":
                    logger.info("File is ACTIVE, proceeding with transcription")
                    break
                elif state_name == "FAILED":
                    logger.error("File processing FAILED on Gemini's side")
                    return ""
                
                if elapsed > max_wait:
                    logger.error(f"File still not active after {max_wait}s")
                    return ""
                
                # Wait before polling again
                await asyncio.sleep(2)
            
            # Use cached model + async generation
            prompt = (
                "Listen to this audio recording carefully and transcribe exactly what the person says. "
                "If you can hear speech, return ONLY the transcribed text with no extra commentary. "
                "If the audio is silent or contains no speech, respond with exactly: NO_SPEECH_DETECTED"
            )
            
            logger.info("Sending transcription request to Gemini...")
            response = await self._model.generate_content_async([prompt, audio_file])
            
            transcription = response.text.strip() if response and response.text else ""
            logger.info(f"Raw transcription result: '{transcription[:200]}'")
            
            # Clean up the uploaded file in background
            try:
                await loop.run_in_executor(None, lambda: genai.delete_file(audio_file.name))
                logger.info("Cleaned up uploaded audio file from Gemini")
            except Exception:
                pass
            
            # Check for empty or "no speech" results
            if not transcription or transcription == "NO_SPEECH_DETECTED":
                logger.warning("No speech detected in audio")
                return ""
            
            logger.info(f"Transcription successful: '{transcription[:100]}...'")
            return transcription
        
        except Exception as e:
            logger.error(f"Error transcribing audio: {type(e).__name__}: {e}")
            return ""

# Create singleton instance
speech_service = SpeechService()
