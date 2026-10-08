from backend.models.schemas import (
    TextQueryRequest,
    HealthResponse,
    ErrorResponse,
    PossibleCondition
)
from backend.services.llm_service import llm_service
from backend.services.vision_service import vision_service
from backend.services.speech_service import speech_service
from backend.services.tts_service import tts_service
from backend.utils.file_handler import file_handler
from backend.utils.logger import logger

router = APIRouter(prefix="/api", tags=["health"])


def _parse_conditions(raw_conditions: list) -> list:
    """Safely parse conditions from LLM response into PossibleCondition objects."""
    conditions = []
    for condition in raw_conditions:
        try:
            if isinstance(condition, dict):
                conditions.append(PossibleCondition(**condition))
            elif isinstance(condition, str):
                conditions.append(PossibleCondition(
                    name=condition, likelihood="possible", description=condition
                ))
        except Exception:
            pass
    return conditions


@router.post("/query", response_model=HealthResponse)
async def text_query(request: TextQueryRequest):
    """Process text-based medical query."""
    try:
        logger.info(f"Processing text query: {request.query[:100]}...")
        
        # Generate LLM response
        llm_result = await llm_service.generate_response(user_query=request.query)
        
        # Parse conditions
        conditions = _parse_conditions(llm_result.get("possible_conditions", []))
        
        # Generate audio if requested
        audio_url = None
        if request.include_audio:
            try:
                audio_path = await tts_service.generate_speech(llm_result.get("explanation", ""))
                audio_url = f"/api/audio/{audio_path.name}"
            except Exception as tts_err:
                logger.error(f"TTS failed: {tts_err}")
        
        return HealthResponse(
            success=True,
            explanation=llm_result.get("explanation", ""),
            possible_conditions=conditions,
            precautions=llm_result.get("precautions", []),
            audio_url=audio_url
        )
    
    except Exception as e:
        logger.error(f"Error processing text query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-image", response_model=HealthResponse)
async def analyze_image(
    image: UploadFile = File(...),
    query: Optional[str] = Form(None),
    include_audio: bool = Form(False)
):
    """Analyze uploaded medical image.
    
    Optimized: Uses a SINGLE Gemini Vision call that returns
    both image analysis and structured health response directly.
    No second LLM call needed.
    """
    try:
        logger.info(f"Processing image analysis: {image.filename}")
        
        # Read and validate image
        image_bytes = await image.read()
        is_valid, error_msg = file_handler.validate_image(image.content_type, len(image_bytes))
        
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Preprocess image (resize/compress for faster upload)
        processed_image = file_handler.preprocess_image(image_bytes)
        
        # Single call: analyze image AND get structured health response
        llm_result = await vision_service.analyze_image_full(processed_image, query)
        
        # Parse conditions
        conditions = _parse_conditions(llm_result.get("possible_conditions", []))
        
        # Generate audio if requested
        audio_url = None
        if include_audio:
            try:
                audio_path = await tts_service.generate_speech(llm_result.get("explanation", ""))
                audio_url = f"/api/audio/{audio_path.name}"
            except Exception as tts_err:
                logger.error(f"TTS failed: {tts_err}")
        
        return HealthResponse(
            success=True,
            explanation=llm_result.get("explanation", ""),
            possible_conditions=conditions,
            precautions=llm_result.get("precautions", []),
            audio_url=audio_url
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing image: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/voice-query", response_model=HealthResponse)
async def voice_query(
    audio: UploadFile = File(...),
    include_audio: bool = Form(True)
):
    """Process voice-based medical query.
    
    Flow: transcribe audio -> validate transcription -> generate LLM response -> optional TTS.
    """
    try:
        logger.info(f"Processing voice query: {audio.filename} (content_type: {audio.content_type})")
        
        # Read and validate audio
        audio_bytes = await audio.read()
        logger.info(f"Audio file size: {len(audio_bytes)} bytes")
        is_valid, error_msg = file_handler.validate_audio(audio.content_type, len(audio_bytes))
        
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Determine file extension from the uploaded filename or content type
        import os as _os
        ext = _os.path.splitext(audio.filename or '')[1] or '.webm'
        if not ext.startswith('.'):
            ext = '.' + ext
        
        # Save temporary audio file with correct extension
        audio_path = file_handler.save_temp_file(audio_bytes, ext)
        logger.info(f"Saved audio to: {audio_path}")
        
        try:
            # Step 1: Transcribe audio
            transcription = await speech_service.transcribe_audio(audio_path)
            logger.info(f"Transcription result: '{transcription[:200] if transcription else '(empty)'}...'")
            
            # Validate transcription — if empty, let the user know
            if not transcription or not transcription.strip():
                logger.warning("Transcription was empty — no speech detected")
                return HealthResponse(
                    success=True,
                    explanation="No speech was detected in your recording. Please try again and speak clearly into the microphone for at least 3-5 seconds.",
                    possible_conditions=[],
                    precautions=[
                        "Make sure your microphone is working and not muted.",
                        "Speak clearly and at a normal volume.",
                        "Record for at least 3-5 seconds.",
                        "Try reducing background noise."
                    ],
                    metadata={"transcription": "(no speech detected)"}
                )
            
            # Step 2: Generate LLM response from transcription
            llm_result = await llm_service.generate_response(voice_transcription=transcription)
            
            # Parse conditions safely
            conditions = _parse_conditions(llm_result.get("possible_conditions", []))
            
            # Step 3: Generate audio response if requested
            audio_url = None
            if include_audio:
                try:
                    audio_path_tts = await tts_service.generate_speech(llm_result.get("explanation", ""))
                    audio_url = f"/api/audio/{audio_path_tts.name}"
                except Exception as tts_err:
                    logger.error(f"TTS failed: {tts_err}")
            
            return HealthResponse(
                success=True,
                explanation=llm_result.get("explanation", ""),
                possible_conditions=conditions,
                precautions=llm_result.get("precautions", []),
                audio_url=audio_url,
                metadata={"transcription": transcription}
            )
        
        finally:
            # Cleanup temp file
            # file_handler.cleanup_file(audio_path)
            pass
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing voice query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/multimodal-query", response_model=HealthResponse)
async def multimodal_query(
    query: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    audio: Optional[UploadFile] = File(None),
    include_audio: bool = Form(False)
):
    """Process multimodal query (combination of text, image, and/or voice)."""
    try:
        logger.info("Processing multimodal query")
        
        image_analysis = None
        transcription = None
        temp_files = []
        
        # Process image if provided
        if image:
            image_bytes = await image.read()
            is_valid, error_msg = file_handler.validate_image(image.content_type, len(image_bytes))
            
            if not is_valid:
                raise HTTPException(status_code=400, detail=f"Image validation failed: {error_msg}")
            
            processed_image = file_handler.preprocess_image(image_bytes)
            image_analysis = await vision_service.analyze_image(processed_image, query)
        
        # Process audio if provided
        if audio:
            audio_bytes = await audio.read()
            is_valid, error_msg = file_handler.validate_audio(audio.content_type, len(audio_bytes))
            
            if not is_valid:
                raise HTTPException(status_code=400, detail=f"Audio validation failed: {error_msg}")
            
            audio_path = file_handler.save_temp_file(audio_bytes, '.webm')
            temp_files.append(audio_path)
            
            transcription = await speech_service.transcribe_audio(audio_path)
        
        try:
            # Generate LLM response with all inputs
            llm_result = await llm_service.generate_response(
                user_query=query,
                image_analysis=image_analysis,
                voice_transcription=transcription
            )
            
            # Parse conditions safely
            conditions = _parse_conditions(llm_result.get("possible_conditions", []))
            
            # Generate audio response
            audio_url = None
            if include_audio:
                try:
                    audio_path_tts = await tts_service.generate_speech(llm_result.get("explanation", ""))
                    audio_url = f"/api/audio/{audio_path_tts.name}"
                except Exception as tts_err:
                    logger.error(f"TTS failed: {tts_err}")
            
            metadata = {}
            if image_analysis:
                metadata["image_analysis"] = image_analysis
            if transcription:
                metadata["transcription"] = transcription
            
            return HealthResponse(
                success=True,
                explanation=llm_result.get("explanation", ""),
                possible_conditions=conditions,
                precautions=llm_result.get("precautions", []),
                audio_url=audio_url,
                metadata=metadata
            )
        
        finally:
            # Cleanup temp files
            for temp_file in temp_files:
                file_handler.cleanup_file(temp_file)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing multimodal query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audio/{filename}")
async def get_audio(filename: str):
    """Serve generated audio file."""
    from pathlib import Path
    audio_path = Path("backend/static/audio") / filename
    
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    return FileResponse(audio_path, media_type="audio/mpeg")


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Multimodal AI Healthcare Assistant",
        "version": "1.0.0"
    }
