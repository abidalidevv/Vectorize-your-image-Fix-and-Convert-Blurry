"""
VectorForge AI — Engine Selector
Routes images to the appropriate vectorization engine based on mode and content analysis.
"""
import logging
from pathlib import Path
import cv2

from vectorization.vtracer_engine import VTracerEngine
from vectorization.contour_engine import ContourEngine
from image_processing.line_detector import detect_line_art

logger = logging.getLogger(__name__)

_vtracer_engine = VTracerEngine()
_contour_engine = ContourEngine()


def select_and_trace(
    image_path: Path,
    output_svg_path: Path,
    params: dict,
) -> dict:
    """
    Select the best engine based on image_mode and trace the image.
    Automatically detects fine line art and activates line preservation.
    """
    mode = params.get("image_mode", "auto")

    # If auto mode, inspect whether the image is monochrome line art
    if mode == "auto":
        try:
            img = cv2.imread(str(image_path), cv2.IMREAD_UNCHANGED)
            if img is not None:
                analysis = detect_line_art(img)
                if analysis["has_fine_lines"] or (analysis["is_monochrome"] and analysis["is_line_art"]):
                    mode = "bw"
                    logger.info("Auto-detected monochrome line art -> routing to BW line-preservation mode")
        except Exception as e:
            logger.warning(f"Auto-detection check failed: {e}")

    # B&W / Sketch mode -> line-preserving tracing
    if mode in ("bw", "sketch"):
        logger.info(f"Engine: VTracer/BW (mode={mode})")
        result = _vtracer_engine.trace_bw(image_path, output_svg_path, params)
        if not result["success"]:
            logger.warning("VTracer/BW failed, falling back to ContourEngine")
            result = _contour_engine.trace(image_path, output_svg_path, params)
        return result

    # All other modes (color, logo, photo) -> VTracer color mode
    logger.info(f"Engine: VTracer (color, mode={mode})")
    result = _vtracer_engine.trace(image_path, output_svg_path, params)

    if not result["success"]:
        logger.warning("VTracer failed, falling back to ContourEngine")
        result = _contour_engine.trace(image_path, output_svg_path, params)

    return result
