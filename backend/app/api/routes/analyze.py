"""
VectorForge AI — Analyze Route
"""
import logging
from fastapi import APIRouter, HTTPException
from models.requests import AnalyzeParams
from core.session import session_manager
from image_processing.analyzer import analyze_image

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/analyze")
async def analyze(params: AnalyzeParams):
    """
    Analyze the uploaded image and return characteristics + mode recommendation.
    """
    session = session_manager.get_session(params.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    if not session.original_path or not session.original_path.exists():
        raise HTTPException(status_code=400, detail="No image uploaded for this session")

    try:
        result = analyze_image(session.original_path)
        result["session_id"] = params.session_id
        return result
    except Exception as e:
        logger.error(f"Analysis failed for session {params.session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
