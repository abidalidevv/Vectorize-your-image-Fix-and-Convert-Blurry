"""
VectorForge AI — Upload Route
"""
import logging
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from core.session import session_manager
from utils.file_utils import validate_upload_file, sanitize_filename
from core.config import settings
from PIL import Image

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    """
    Upload a raster image and create a new processing session.
    Returns session_id and image metadata.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    content = await file.read()

    # Validate
    validation = validate_upload_file(
        file.filename, content, settings.max_upload_size_mb
    )
    if not validation["ok"]:
        raise HTTPException(status_code=400, detail=validation["error"])

    # Create session
    session = session_manager.create_session()
    safe_name = sanitize_filename(file.filename)
    ext = Path(file.filename).suffix.lower()
    original_path = session.get_path("original", ext)

    # Write original file
    original_path.write_bytes(content)

    # Extract image metadata using Pillow
    try:
        pil_img = Image.open(original_path)
        w, h = pil_img.size
        fmt = pil_img.format or ext.lstrip(".").upper()
        has_alpha = pil_img.mode in ("RGBA", "LA", "PA")
        mode = pil_img.mode
    except Exception as e:
        session.cleanup()
        raise HTTPException(status_code=400, detail=f"Cannot read image: {e}")

    # Reject extremely large images
    if w > settings.max_image_dimension or h > settings.max_image_dimension:
        session.cleanup()
        raise HTTPException(
            status_code=400,
            detail=f"Image too large ({w}×{h}). Maximum dimension: {settings.max_image_dimension}px",
        )

    # Reject tiny images
    if w < settings.min_image_size or h < settings.min_image_size:
        session.cleanup()
        raise HTTPException(status_code=400, detail=f"Image too small ({w}×{h})")

    # Update session metadata
    session.original_path = original_path
    session.original_filename = safe_name
    session.image_width = w
    session.image_height = h
    session.image_format = fmt
    session.has_alpha = has_alpha

    # Build preview URL (served from /temp/<session_id>/<filename>)
    preview_url = f"/temp/{session.session_id}/{original_path.name}"

    logger.info(f"Uploaded: {safe_name} ({w}×{h}) → session {session.session_id}")

    return {
        "session_id": session.session_id,
        "filename": safe_name,
        "width": w,
        "height": h,
        "file_size_bytes": len(content),
        "format": fmt,
        "has_alpha": has_alpha,
        "mode": mode,
        "preview_url": preview_url,
    }


@router.get("/session/{session_id}/status")
async def session_status(session_id: str):
    """Check if a session is still alive and return its current state for rehydration."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    return {
        "session_id": session.session_id,
        "filename": session.original_filename,
        "width": session.image_width,
        "height": session.image_height,
        "format": session.image_format,
        "has_alpha": session.has_alpha,
        "has_original": bool(session.original_path and session.original_path.exists()),
        "has_preprocessed": bool(session.preprocessed_path and session.preprocessed_path.exists()),
        "has_quantized": bool(session.quantized_path and session.quantized_path.exists()),
        "has_vector": bool(session.svg_path and session.svg_path.exists()),
        "original_url": f"/temp/{session.session_id}/{session.original_path.name}" if session.original_path else None,
        "preprocessed_url": f"/temp/{session.session_id}/{session.preprocessed_path.name}" if session.preprocessed_path else None,
        "quantized_url": f"/temp/{session.session_id}/{session.quantized_path.name}" if session.quantized_path else None,
    }

