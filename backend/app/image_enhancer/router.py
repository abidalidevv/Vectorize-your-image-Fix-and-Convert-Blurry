"""
VectorForge AI — Image Enhancement Route
"""
import logging
from fastapi import APIRouter, HTTPException
from models.requests import EnhanceParams
from core.session import session_manager
from image_enhancer.engine import apply_enhancement

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/enhance")
async def enhance_image(params: EnhanceParams):
    """
    Apply super-resolution upscaling, deblurring, sharpening, CLAHE tone,
    and color enhancement to the uploaded image.
    """
    session = session_manager.get_session(params.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    if not session.original_path or not session.original_path.exists():
        raise HTTPException(status_code=400, detail="No image uploaded for this session")

    output_path = session.get_path("enhanced", ".png")

    try:
        changes, out_w, out_h = apply_enhancement(
            session.original_path,
            params.model_dump(),
            output_path,
        )
        session.enhanced_path = output_path
        preview_url = f"/temp/{session.session_id}/{output_path.name}"

        return {
            "session_id": params.session_id,
            "preview_url": preview_url,
            "width": out_w,
            "height": out_h,
            "changes_applied": changes if changes else ["No changes"],
        }
    except Exception as e:
        logger.error(f"Image enhancement failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Enhancement failed: {str(e)}")
