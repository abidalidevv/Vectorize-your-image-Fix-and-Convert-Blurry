"""
VectorForge AI — Contour Engine
OpenCV contour-based B&W/sketch tracing with cubic Bézier fitting.
Used as fallback for monochrome images.
"""
import logging
from pathlib import Path
import re
import xml.etree.ElementTree as ET

import cv2
import numpy as np
from PIL import Image

from vectorization.base import AbstractTracer

logger = logging.getLogger(__name__)


class ContourEngine(AbstractTracer):
    """
    OpenCV contour-based vectorization engine.
    Best suited for B&W line art and simple silhouettes.
    """

    @property
    def name(self) -> str:
        return "ContourTracer"

    @property
    def supports_color(self) -> bool:
        return False

    def trace(self, image_path: Path, output_svg_path: Path, params: dict) -> dict:
        try:
            pil_img = Image.open(image_path).convert("RGB")
            img = np.array(pil_img)
            h, w = img.shape[:2]

            # Grayscale + threshold
            gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

            # Adaptive threshold for sketches, Otsu for clean B&W
            use_adaptive = params.get("image_mode") == "sketch"
            if use_adaptive:
                block = 25
                binary = cv2.adaptiveThreshold(
                    gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                    cv2.THRESH_BINARY_INV, block, 5
                )
            else:
                _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

            # Noise cleanup (only if requested)
            speckle = int(params.get("filter_speckle", 0))
            if speckle > 1:
                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (speckle, speckle))
                binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

            # Find contours
            contours, hierarchy = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_TC89_L1)

            min_area = float(params.get("min_area", 1.0))
            simplify_tol = float(params.get("simplify_tolerance", 0.005))

            # Build SVG paths
            svg_paths = []
            for i, contour in enumerate(contours):
                area = cv2.contourArea(contour)
                if area < min_area:
                    continue

                epsilon = simplify_tol * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, max(epsilon, 0.1), True)

                if len(approx) < 2:
                    continue

                path_d = _contour_to_path_d(approx)
                svg_paths.append(f'  <path d="{path_d}" fill="#000000" fill-rule="evenodd"/>')

            svg_content = _build_svg(w, h, svg_paths)
            output_svg_path.write_text(svg_content, encoding="utf-8")

            logger.info(f"ContourTracer: {len(svg_paths)} paths → {output_svg_path}")
            return {
                "success": True,
                "engine": self.name,
                "error": None,
                "svg_size": len(svg_content),
            }

        except Exception as e:
            logger.error(f"ContourEngine failed: {e}", exc_info=True)
            return {"success": False, "engine": self.name, "error": str(e), "svg_size": 0}


def _contour_to_path_d(contour: np.ndarray) -> str:
    """Convert OpenCV contour to SVG path 'd' attribute."""
    points = contour.squeeze()
    if points.ndim == 1:
        points = points.reshape(1, -1)

    parts = [f"M {points[0][0]} {points[0][1]}"]
    for pt in points[1:]:
        parts.append(f"L {pt[0]} {pt[1]}")
    parts.append("Z")
    return " ".join(parts)


def _build_svg(width: int, height: int, paths: list[str]) -> str:
    """Assemble a minimal valid SVG document."""
    paths_str = "\n".join(paths)
    return (
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}">\n'
        f'  <rect width="{width}" height="{height}" fill="white"/>\n'
        f'{paths_str}\n'
        f'</svg>'
    )
