"""
VectorForge AI — Remove Background Route
"""
import logging
from fastapi import APIRouter, HTTPException
from models.requests import RemoveBgParams
from core.session import session_manager
from bg_remover.engine import remove_image_background

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/remove-bg")
async def remove_bg(params: RemoveBgParams):
    """
    Remove background from image with AI or color flood-fill segmentation,
    edge matting, defringe choke, and optional replacement backdrop.
    """
    session = session_manager.get_session(params.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    if not session.original_path or not session.original_path.exists():
        raise HTTPException(status_code=400, detail="No image uploaded for this session")

    output_path = session.get_path("bg_removed", ".png")

    try:
        changes, out_w, out_h = remove_image_background(
            session.original_path,
            params.model_dump(),
            output_path,
        )
        session.bg_removed_path = output_path
        preview_url = f"/temp/{session.session_id}/{output_path.name}"

        return {
            "session_id": params.session_id,
            "preview_url": preview_url,
            "width": out_w,
            "height": out_h,
            "changes_applied": changes if changes else ["Background removed"],
        }
    except Exception as e:
        logger.error(f"Remove background failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Background removal failed: {str(e)}")
