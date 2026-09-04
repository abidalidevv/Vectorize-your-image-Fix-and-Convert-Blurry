"""
VectorForge AI — Engine Selector
Routes images to the appropriate vectorization engine.
"""
import logging
from pathlib import Path
from typing import Literal

from vectorization.vtracer_engine import VTracerEngine
from vectorization.contour_engine import ContourEngine

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
    Returns result dict from the engine.
    """
    mode = params.get("image_mode", "auto")

    # If BW mode → VTracer binary mode is cleanest
    if mode == "bw":
        logger.info("Engine: VTracer/BW (binary mode)")
        result = _vtracer_engine.trace_bw(image_path, output_svg_path, params)
        if not result["success"]:
            # Fallback to contour engine
            logger.warning("VTracer/BW failed, falling back to ContourEngine")
            result = _contour_engine.trace(image_path, output_svg_path, params)
        return result

    # All other modes → VTracer color mode
    logger.info(f"Engine: VTracer (color, mode={mode})")
    result = _vtracer_engine.trace(image_path, output_svg_path, params)

    if not result["success"]:
        # Fallback to contour for B&W
        logger.warning("VTracer failed, falling back to ContourEngine")
        result = _contour_engine.trace(image_path, output_svg_path, params)

    return result
