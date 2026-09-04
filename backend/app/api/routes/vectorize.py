"""
VectorForge AI — Vectorize Route
"""
import logging
import time
from pathlib import Path
from fastapi import APIRouter, HTTPException
from models.requests import VectorizeParams
from core.session import session_manager
from vectorization.engine_selector import select_and_trace
from utils.svg_optimizer import validate_svg, extract_layers_from_svg, optimize_svg, ensure_viewbox

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/vectorize")
async def vectorize(params: VectorizeParams):
    """
    Vectorize the current image in the session pipeline.
    Uses quantized → preprocessed → original (in that priority order).
    """
    session = session_manager.get_session(params.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    # Select source image (best available stage)
    source_path = _pick_source(session, params)
    if source_path is None:
        raise HTTPException(status_code=400, detail="No image available for vectorization")

    output_svg_path = session.get_path("vector", ".svg")
    t_start = time.time()

    try:
        result = select_and_trace(
            source_path,
            output_svg_path,
            params.model_dump(),
        )

        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"Vectorization failed: {result.get('error', 'Unknown error')}",
            )

        session.svg_path = output_svg_path
        elapsed_ms = int((time.time() - t_start) * 1000)

        # Read SVG and ensure viewBox attribute for crisp scaling
        svg_content = output_svg_path.read_text(encoding="utf-8")
        svg_content = ensure_viewbox(svg_content)
        output_svg_path.write_text(svg_content, encoding="utf-8")

        # Validate and get stats
        validation = validate_svg(svg_content)
        stats = validation["stats"]

        # Extract layer info
        layers = extract_layers_from_svg(svg_content)

        svg_url = f"/temp/{session.session_id}/{output_svg_path.name}"

        # Embed as data URL for inline preview
        import base64
        svg_b64 = base64.b64encode(svg_content.encode("utf-8")).decode("ascii")
        svg_data_url = f"data:image/svg+xml;base64,{svg_b64}"

        return {
            "session_id": params.session_id,
            "svg_url": svg_url,
            "svg_data_url": svg_data_url,
            "stats": stats,
            "layers": layers,
            "engine_used": result.get("engine", "unknown"),
            "processing_time_ms": elapsed_ms,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Vectorize failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Vectorization failed: {str(e)}")


@router.get("/svg/{session_id}")
async def get_svg(session_id: str):
    """Serve the current SVG for a session."""
    from fastapi.responses import Response
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if not session.svg_path or not session.svg_path.exists():
        raise HTTPException(status_code=404, detail="No SVG generated yet")
    content = session.svg_path.read_text(encoding="utf-8")
    return Response(content=content, media_type="image/svg+xml")


def _pick_source(session, params: VectorizeParams) -> Path | None:
    """Pick source image based on explicit user choice, falling back sensibly."""
    stage = getattr(params, "source_stage", "auto")
    if stage == "original":
        return session.original_path if session.original_path and session.original_path.exists() else None
    if stage == "preprocessed":
        if session.preprocessed_path and session.preprocessed_path.exists():
            return session.preprocessed_path
        return session.original_path
    if stage == "quantized":
        if session.quantized_path and session.quantized_path.exists():
            return session.quantized_path
        return session.preprocessed_path or session.original_path
    # auto: prefer original unless the user is in logo mode AND explicitly quantized
    if params.image_mode == "logo" and session.quantized_path and session.quantized_path.exists():
        return session.quantized_path
    if session.preprocessed_path and session.preprocessed_path.exists():
        return session.preprocessed_path
    return session.original_path
