"""
VectorForge AI — Quantize Route
"""
import logging
from fastapi import APIRouter, HTTPException
from models.requests import QuantizeParams
from core.session import session_manager
from image_processing.quantizer import quantize_image

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/quantize")
async def quantize(params: QuantizeParams):
    """
    Reduce image to a fixed color palette.
    """
    session = session_manager.get_session(params.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    # Use preprocessed if available, otherwise original
    if params.use_preprocessed and session.preprocessed_path and session.preprocessed_path.exists():
        source_path = session.preprocessed_path
    elif session.original_path and session.original_path.exists():
        source_path = session.original_path
    else:
        raise HTTPException(status_code=400, detail="No image available for quantization")

    output_path = session.get_path("quantized", ".png")

    try:
        result = quantize_image(
            source_path,
            output_path,
            num_colors=params.num_colors,
            method=params.method,
        )
        session.quantized_path = output_path
        preview_url = f"/temp/{session.session_id}/{output_path.name}"

        return {
            "session_id": params.session_id,
            "num_colors": result["num_colors"],
            "palette": result["palette"],
            "preview_url": preview_url,
        }
    except Exception as e:
        logger.error(f"Quantize failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Quantization failed: {str(e)}")
