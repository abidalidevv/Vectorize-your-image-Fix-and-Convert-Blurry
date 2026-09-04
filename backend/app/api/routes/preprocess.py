"""
VectorForge AI — Preprocess Route
"""
import logging
from fastapi import APIRouter, HTTPException
from models.requests import PreprocessParams
from core.session import session_manager
from image_processing.preprocessor import apply_preprocessing

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/preprocess")
async def preprocess(params: PreprocessParams):
    """
    Apply preprocessing pipeline to the uploaded image.
    """
    session = session_manager.get_session(params.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    if not session.original_path or not session.original_path.exists():
        raise HTTPException(status_code=400, detail="No image uploaded for this session")

    output_path = session.get_path("preprocessed", ".png")

    try:
        changes = apply_preprocessing(
            session.original_path,
            params.model_dump(),
            output_path,
        )
        session.preprocessed_path = output_path
        preview_url = f"/temp/{session.session_id}/{output_path.name}"

        return {
            "session_id": params.session_id,
            "preview_url": preview_url,
            "changes_applied": changes if changes else ["No changes (default parameters)"],
        }
    except Exception as e:
        logger.error(f"Preprocess failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Preprocessing failed: {str(e)}")
