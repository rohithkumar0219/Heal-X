from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pathlib import Path
import os
import sys
from dotenv import load_dotenv

# Load environment variables from parent directory
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from routes.health_routes import router as health_router
from utils.logger import logger

# Create FastAPI app
app = FastAPI(
    title="Multimodal AI Healthcare Assistant",
    description="AI-powered healthcare assistant with text, image, and voice capabilities",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS configuration
origins = os.getenv("CORS_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create necessary directories
Path("backend/static/audio").mkdir(parents=True, exist_ok=True)
Path("logs").mkdir(exist_ok=True)
Path("temp_uploads").mkdir(exist_ok=True)

# Mount static files
frontend_path = Path(__file__).parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")

# Include routers
app.include_router(health_router)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc)
        }
    )

# Root endpoint
@app.get("/")
async def root():
    """Redirect to frontend."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/static/index.html")

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Multimodal AI Healthcare Assistant starting up...")
    logger.info(f"API Documentation: http://localhost:{os.getenv('PORT', 8000)}/api/docs")
    
    # Verify API key
    if not os.getenv("OPENAI_API_KEY"):
        logger.warning("OPENAI_API_KEY not set! Please configure your .env file.")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Multimodal AI Healthcare Assistant...")
    
    # Cleanup old files
    from utils.file_handler import file_handler
    file_handler.cleanup_old_files(max_age_hours=1)

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
