"""
VectorForge AI — FastAPI Backend Entry Point
"""
import sys
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.config import settings
from core.session import session_manager
from api.routes import upload, analyze, preprocess, quantize, vectorize, export

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("vectorforge")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle — startup and shutdown."""
    logger.info("VectorForge AI backend starting...")
    settings.temp_dir.mkdir(parents=True, exist_ok=True)
    yield
    logger.info("VectorForge AI backend shutting down. Cleaning temp files...")
    session_manager.cleanup_all()


app = FastAPI(
    title="VectorForge AI",
    description="Local-first raster-to-vector conversion engine",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount temp files for direct preview access
app.mount("/temp", StaticFiles(directory=str(settings.temp_dir)), name="temp")

# Register routers
app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(analyze.router, prefix="/api", tags=["analyze"])
app.include_router(preprocess.router, prefix="/api", tags=["preprocess"])
app.include_router(quantize.router, prefix="/api", tags=["quantize"])
app.include_router(vectorize.router, prefix="/api", tags=["vectorize"])
app.include_router(export.router, prefix="/api", tags=["export"])


@app.get("/health", tags=["health"])
async def health_check():
    return {
        "status": "ok",
        "version": "1.0.0",
        "service": "VectorForge AI",
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"},
    )
