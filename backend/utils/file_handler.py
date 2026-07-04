import os
import uuid
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image
import io

from utils.logger import logger

class FileHandler:
    """Handles file validation, processing, and cleanup."""
    
    def __init__(self, max_image_size: int = 10485760, max_audio_size: int = 26214400):
        """
        Initialize FileHandler.
        
        Args:
            max_image_size: Maximum image size in bytes (default 10MB)
            max_audio_size: Maximum audio size in bytes (default 25MB)
        """
        self.max_image_size = max_image_size
        self.max_audio_size = max_audio_size
        self.allowed_image_types = {'image/jpeg', 'image/png', 'image/jpg'}
        self.allowed_audio_types = {'audio/wav', 'audio/mpeg', 'audio/webm', 'audio/mp4', 'audio/x-m4a', 'audio/ogg'}
        
        # Create temp directory
        self.temp_dir = Path("temp_uploads")
        self.temp_dir.mkdir(exist_ok=True)
    
    def validate_image(self, content_type: str, file_size: int) -> Tuple[bool, Optional[str]]:
        """
        Validate image file.
        
        Args:
            content_type: MIME type of the file
            file_size: Size of file in bytes
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if content_type not in self.allowed_image_types:
            return False, f"Invalid image type. Allowed: {', '.join(self.allowed_image_types)}"
        
        if file_size > self.max_image_size:
            return False, f"Image too large. Max size: {self.max_image_size / 1024 / 1024}MB"
        
        return True, None
    
    def validate_audio(self, content_type: str, file_size: int) -> Tuple[bool, Optional[str]]:
        """
        Validate audio file.
        
        Args:
            content_type: MIME type of the file (may include codec params like 'audio/webm;codecs=opus')
            file_size: Size of file in bytes
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Strip codec parameters (e.g. 'audio/webm;codecs=opus' -> 'audio/webm')
        base_type = content_type.split(';')[0].strip().lower() if content_type else ''
        
        if base_type not in self.allowed_audio_types:
            logger.warning(f"Audio type rejected: '{content_type}' (base: '{base_type}')")
            return False, f"Invalid audio type '{content_type}'. Allowed: {', '.join(self.allowed_audio_types)}"
        
        if file_size > self.max_audio_size:
            return False, f"Audio too large. Max size: {self.max_audio_size / 1024 / 1024}MB"
        
        return True, None
    
    def preprocess_image(self, image_bytes: bytes, max_size: Tuple[int, int] = (1024, 1024)) -> bytes:
        """
        Preprocess image: resize and optimize.
        
        Args:
            image_bytes: Raw image bytes
            max_size: Maximum dimensions (width, height)
        
        Returns:
            Processed image bytes
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert RGBA to RGB if necessary
            if image.mode == 'RGBA':
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[3])
                image = background
            
            # Resize if larger than max_size
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Save to bytes
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=85, optimize=True)
            return output.getvalue()
        
        except Exception as e:
            logger.error(f"Error preprocessing image: {e}")
            return image_bytes
    
    def save_temp_file(self, file_bytes: bytes, extension: str) -> Path:
        """
        Save file to temporary directory.
        
        Args:
            file_bytes: File content
            extension: File extension (e.g., '.jpg', '.mp3')
        
        Returns:
            Path to saved file
        """
        filename = f"{uuid.uuid4()}{extension}"
        filepath = self.temp_dir / filename
        
        with open(filepath, 'wb') as f:
            f.write(file_bytes)
        
        logger.info(f"Saved temp file: {filepath}")
        return filepath
    
    def cleanup_file(self, filepath: Path) -> None:
        """
        Delete temporary file.
        
        Args:
            filepath: Path to file to delete
        """
        try:
            if filepath.exists():
                filepath.unlink()
                logger.info(f"Cleaned up file: {filepath}")
        except Exception as e:
            logger.error(f"Error cleaning up file {filepath}: {e}")
    
    def cleanup_old_files(self, max_age_hours: int = 24) -> None:
        """
        Clean up old temporary files.
        
        Args:
            max_age_hours: Maximum age of files to keep in hours
        """
        import time
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        for filepath in self.temp_dir.iterdir():
            if filepath.is_file():
                file_age = current_time - filepath.stat().st_mtime
                if file_age > max_age_seconds:
                    self.cleanup_file(filepath)

# Create singleton instance
file_handler = FileHandler()
