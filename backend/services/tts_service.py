import os
from pathlib import Path
from gtts import gTTS
from utils.logger import logger
import uuid

class TTSService:
    """Service for text-to-speech conversion."""
    
    def __init__(self):
        """Initialize TTS service."""
        self.output_dir = Path("backend/static/audio")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def generate_speech(self, text: str, language: str = "en") -> Path:
        """
        Convert text to speech audio file.
        
        Args:
            text: Text to convert to speech
            language: Language code (default: 'en')
        
        Returns:
            Path to generated audio file
        """
        try:
            logger.info(f"Generating speech for text: {text[:100]}...")
            
            # Generate unique filename
            filename = f"response_{uuid.uuid4()}.mp3"
            filepath = self.output_dir / filename
            
            # Create TTS
            tts = gTTS(text=text, lang=language, slow=False)
            tts.save(str(filepath))
            
            logger.info(f"Speech generated: {filepath}")
            return filepath
        
        except Exception as e:
            logger.error(f"Error generating speech: {e}")
            raise Exception(f"Failed to generate speech: {str(e)}")
    
    def cleanup_audio(self, filepath: Path) -> None:
        """
        Delete audio file.
        
        Args:
            filepath: Path to audio file
        """
        try:
            if filepath.exists():
                filepath.unlink()
                logger.info(f"Cleaned up audio file: {filepath}")
        except Exception as e:
            logger.error(f"Error cleaning up audio: {e}")

# Create singleton instance
tts_service = TTSService()
