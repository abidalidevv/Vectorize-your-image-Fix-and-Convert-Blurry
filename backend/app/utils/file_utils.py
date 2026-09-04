"""
VectorForge AI — File Utilities
Security-focused file handling.
"""
import re
import hashlib
import mimetypes
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}
ALLOWED_MIME_PREFIXES = {"image/png", "image/jpeg", "image/bmp", "image/webp", "image/x-bmp"}

# Magic bytes for image format detection (no trusting client MIME)
MAGIC_SIGNATURES = {
    b"\x89PNG": "image/png",
    b"\xff\xd8\xff": "image/jpeg",
    b"BM": "image/bmp",
    b"RIFF": "image/webp",  # combined with offset check
    b"GIF8": None,          # gif — not supported
}


def sanitize_filename(filename: str) -> str:
    """Remove dangerous characters from uploaded filenames."""
    # Strip path separators and null bytes
    name = re.sub(r'[^\w\s\-_.]', '', filename.replace('/', '_').replace('\\', '_'))
    name = name.strip()
    if not name:
        name = "upload"
    return name[:128]


def detect_image_type_from_bytes(data: bytes) -> Optional[str]:
    """Detect image MIME type from file magic bytes."""
    if data[:4] == b"\x89PNG":
        return "image/png"
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:2] == b"BM":
        return "image/bmp"
    # WebP: RIFF????WEBP
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def validate_upload_file(filename: str, content: bytes, max_size_mb: int = 50) -> dict:
    """
    Validate an uploaded file for safety and compatibility.
    Returns dict with 'ok', 'mime', and 'error' keys.
    """
    # Size check
    max_bytes = max_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        return {"ok": False, "error": f"File too large. Maximum is {max_size_mb}MB."}

    if len(content) < 16:
        return {"ok": False, "error": "File too small to be a valid image."}

    # Extension check
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return {"ok": False, "error": f"Extension '{ext}' not allowed. Use: {', '.join(ALLOWED_EXTENSIONS)}"}

    # Magic bytes check
    detected_mime = detect_image_type_from_bytes(content)
    if detected_mime is None:
        return {"ok": False, "error": "File content does not match a supported image format."}

    return {"ok": True, "mime": detected_mime, "error": None}


def compute_file_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:16]
