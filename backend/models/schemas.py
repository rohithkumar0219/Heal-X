from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class TextQueryRequest(BaseModel):
    """Request model for text-based queries."""
    query: str = Field(..., min_length=1, max_length=2000, description="User's medical query")
    include_audio: bool = Field(default=False, description="Whether to include TTS audio response")

class ImageAnalysisRequest(BaseModel):
    """Request model for image analysis."""
    query: Optional[str] = Field(None, max_length=1000, description="Additional context or question")
    include_audio: bool = Field(default=False, description="Whether to include TTS audio response")

class VoiceQueryRequest(BaseModel):
    """Request model for voice queries."""
    include_audio: bool = Field(default=True, description="Whether to include TTS audio response")

class MultimodalRequest(BaseModel):
    """Request model for multimodal queries."""
    query: Optional[str] = Field(None, max_length=2000, description="Text query")
    include_audio: bool = Field(default=False, description="Whether to include TTS audio response")

class PossibleCondition(BaseModel):
    """Model for a possible medical condition."""
    name: str = Field(..., description="Name of the condition")
    likelihood: str = Field(..., description="Likelihood level (e.g., 'possible', 'likely', 'unlikely')")
    description: str = Field(..., description="Brief description")

class HealthResponse(BaseModel):
    """Response model for health queries."""
    success: bool = Field(..., description="Whether the request was successful")
    explanation: str = Field(..., description="Detailed explanation of the analysis")
    possible_conditions: List[PossibleCondition] = Field(
        default_factory=list,
        description="List of possible conditions (educational only)"
    )
    precautions: List[str] = Field(
        default_factory=list,
        description="Suggested precautions and care tips"
    )
    disclaimer: str = Field(
        default="This information is for educational purposes only and is not a substitute for professional medical advice, diagnosis, or treatment. Always seek the advice of your physician or other qualified health provider with any questions you may have regarding a medical condition.",
        description="Medical disclaimer"
    )
    audio_url: Optional[str] = Field(None, description="URL to audio response (if requested)")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")

class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = Field(default=False)
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    timestamp: datetime = Field(default_factory=datetime.now)

class HealthCheckResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(default_factory=datetime.now)
    version: str = Field(default="1.0.0", description="API version")
