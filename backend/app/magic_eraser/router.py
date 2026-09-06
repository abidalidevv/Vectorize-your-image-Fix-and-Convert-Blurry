"""
VectorForge AI — Magic Eraser & Inpainting Route
"""
import logging
from fastapi import APIRouter, HTTPException
from models.requests import InpaintParams
from core.session import session_manager
from magic_eraser.engine import inpaint_image

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/inpaint")
async def inpaint_object(params: InpaintParams):
    """
    Erase masked objects and naturally reconstruct the background using LaMa inpainting.
    """
    session = session_manager.get_session(params.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    # Use current working stage image (enhanced/cutout if present, otherwise original)
    input_path = session.enhanced_path or session.original_path
    if not input_path or not input_path.exists():
        raise HTTPException(status_code=400, detail="No source image available in session")

    output_path = session.get_path("inpainted", ".png")

    try:
        changes, out_w, out_h = inpaint_image(
            input_path,
            params.mask_data,
            output_path,
            quality=params.quality,
            dilate_radius=params.dilate_radius,
            method=params.method,
        )
        session.enhanced_path = output_path
        preview_url = f"/temp/{session.session_id}/{output_path.name}"

        return {
            "session_id": params.session_id,
            "preview_url": preview_url,
            "width": out_w,
            "height": out_h,
            "changes_applied": changes if changes else ["Magic Eraser complete"],
        }
    except Exception as e:
        logger.error(f"Inpainting failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Inpainting failed: {str(e)}")
