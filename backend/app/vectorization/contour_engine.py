"""
VectorForge AI — Contour Engine
OpenCV contour-based B&W/sketch tracing with two-level hierarchy (RETR_CCOMP)
and compound SVG paths with evenodd fill rule.
"""
import logging
from pathlib import Path
from typing import List

import cv2
import numpy as np
from PIL import Image

from vectorization.base import AbstractTracer
from image_processing.line_detector import enhance_fine_lines

logger = logging.getLogger(__name__)


class ContourEngine(AbstractTracer):
    """
    OpenCV contour-based vectorization engine.
    Produces compound SVG paths with evenodd fill-rule to correctly preserve
    holes, concentric rings, and nested contours.
    """

    @property
    def name(self) -> str:
        return "ContourTracer"

    @property
    def supports_color(self) -> bool:
        return False

    def trace(self, image_path: Path, output_svg_path: Path, params: dict) -> dict:
        try:
            # Check for fine line enhancement
            trace_image_path = image_path
            temp_enhanced_path = None
            if params.get("preserve_fine_lines", True):
                temp_enhanced_path = image_path.parent / f"{image_path.stem}_contour_enhanced.png"
                enhanced_path, was_enhanced = enhance_fine_lines(image_path, temp_enhanced_path)
                if was_enhanced:
                    trace_image_path = enhanced_path

            pil_img = Image.open(trace_image_path).convert("RGB")
            img = np.array(pil_img)
            h, w = img.shape[:2]

            # Grayscale + threshold
            gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

            use_adaptive = params.get("image_mode") == "sketch"
            if use_adaptive:
                block = 25
                binary = cv2.adaptiveThreshold(
                    gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                    cv2.THRESH_BINARY_INV, block, 5
                )
            else:
                _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

            # Noise cleanup
            speckle = int(params.get("filter_speckle", 0))
            if speckle > 1:
                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (speckle, speckle))
                binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

            # Use RETR_CCOMP to get two-level hierarchy (outer boundaries and inner holes)
            contours, hierarchy = cv2.findContours(binary, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_TC89_L1)

            if hierarchy is None or len(contours) == 0:
                svg_content = _build_svg(w, h, [])
                output_svg_path.write_text(svg_content, encoding="utf-8")
                return {"success": True, "engine": self.name, "error": None, "svg_size": len(svg_content)}

            hierarchy = hierarchy[0]
            min_area = float(params.get("min_area", 1.0))
            simplify_tol = float(params.get("simplify_tolerance", 0.002))

            # Build compound SVG paths grouping outer boundary with its child holes
            svg_paths: List[str] = []
            for i, (cnt, hier) in enumerate(zip(contours, hierarchy)):
                next_idx, prev_idx, child_idx, parent_idx = hier
                # Only process top-level outer boundaries
                if parent_idx != -1:
                    continue

                area = cv2.contourArea(cnt)
                arc_len = cv2.arcLength(cnt, True)
                if area < min_area and arc_len < 10.0:
                    continue

                subpaths: List[str] = []
                # Outer contour
                epsilon = max(simplify_tol * arc_len, 0.3)
                approx = cv2.approxPolyDP(cnt, epsilon, True)
                if len(approx) >= 3:
                    subpaths.append(_contour_to_path_d(approx))

                # Traverse all child holes of this outer contour
                curr_hole = child_idx
                while curr_hole != -1:
                    hole_cnt = contours[curr_hole]
                    hole_arc = cv2.arcLength(hole_cnt, True)
                    hole_eps = max(simplify_tol * hole_arc, 0.3)
                    hole_approx = cv2.approxPolyDP(hole_cnt, hole_eps, True)
                    if len(hole_approx) >= 3:
                        subpaths.append(_contour_to_path_d(hole_approx))
                    curr_hole = hierarchy[curr_hole][0]

                if subpaths:
                    compound_d = " ".join(subpaths)
                    svg_paths.append(f'  <path d="{compound_d}" fill="#000000" fill-rule="evenodd"/>')

            # Cleanup temp file
            if temp_enhanced_path and temp_enhanced_path.exists():
                try:
                    temp_enhanced_path.unlink()
                except Exception:
                    pass

            svg_content = _build_svg(w, h, svg_paths)
            output_svg_path.write_text(svg_content, encoding="utf-8")

            logger.info(f"ContourTracer: {len(svg_paths)} compound paths → {output_svg_path}")
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
    """Convert OpenCV contour to SVG path 'd' subpath string (M...L...Z)."""
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
