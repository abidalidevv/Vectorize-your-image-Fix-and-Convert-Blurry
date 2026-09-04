"""
VectorForge AI — Export Route
"""
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, Response
from models.requests import ExportSVGParams, ExportPNGParams
from core.session import session_manager
from export.svg_exporter import export_svg
from export.png_exporter import export_png

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/export/svg")
async def export_svg_endpoint(params: ExportSVGParams):
    """Export the current SVG with optional optimization."""
    session = session_manager.get_session(params.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.svg_path or not session.svg_path.exists():
        raise HTTPException(status_code=400, detail="No SVG to export. Run vectorization first.")

    output_path = session.get_path("export", ".svg")

    try:
        result = export_svg(session.svg_path, output_path, optimize=params.optimize)
        filename = Path(session.original_filename).stem + "_vector.svg"

        return FileResponse(
            path=str(output_path),
            media_type="image/svg+xml",
            filename=filename,
            headers={"X-File-Size": str(result["file_size_bytes"])},
        )
    except Exception as e:
        logger.error(f"SVG export failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"SVG export failed: {str(e)}")


@router.post("/export/png")
async def export_png_endpoint(params: ExportPNGParams):
    """Export rasterized PNG at specified scale."""
    session = session_manager.get_session(params.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.svg_path or not session.svg_path.exists():
        raise HTTPException(status_code=400, detail="No SVG to export. Run vectorization first.")

    output_path = session.get_path(f"export_{params.scale}x", ".png")

    try:
        result = export_png(
            session.svg_path,
            output_path,
            scale=params.scale,
            background_color=params.background_color,
            dpi=params.dpi,
        )
        stem = Path(session.original_filename).stem
        filename = f"{stem}_vector_{params.scale}x.png"

        return FileResponse(
            path=str(output_path),
            media_type="image/png",
            filename=filename,
            headers={"X-File-Size": str(result["file_size_bytes"])},
        )
    except Exception as e:
        logger.error(f"PNG export failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"PNG export failed: {str(e)}")


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Clean up session and temp files."""
    session_manager.delete_session(session_id)
    return {"status": "deleted", "session_id": session_id}
