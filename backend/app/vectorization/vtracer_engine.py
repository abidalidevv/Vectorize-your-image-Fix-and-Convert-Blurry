"""
VectorForge AI / Vectorizer AI — VTracer Engine
Primary color and line-art vectorization using the vtracer library (Rust-based).
Features fine-line supersampling preservation (anti-bulging/anti-flaring) and cutout hierarchy.
"""
import logging
from pathlib import Path
import re
from typing import Any
import cv2
import vtracer

from vectorization.base import AbstractTracer
from image_processing.line_detector import enhance_fine_lines, detect_line_art

logger = logging.getLogger(__name__)


# Quality preset → vtracer parameter mappings
QUALITY_PRESETS = {
    "fast": {
        "colormode": "color",
        "hierarchical": "stacked",
        "mode": "polygon",
        "filter_speckle": 2,
        "color_precision": 4,
        "layer_difference": 24,
        "corner_threshold": 60,
        "length_threshold": 4.0,
        "max_iterations": 5,
        "splice_threshold": 45,
        "path_precision": 3,
    },
    "balanced": {
        "colormode": "color",
        "hierarchical": "stacked",
        "mode": "spline",
        "filter_speckle": 1,
        "color_precision": 7,
        "layer_difference": 16,
        "corner_threshold": 60,
        "length_threshold": 2.5,
        "max_iterations": 10,
        "splice_threshold": 45,
        "path_precision": 5,
    },
    "high": {
        "colormode": "color",
        "hierarchical": "stacked",
        "mode": "spline",
        "filter_speckle": 1,
        "color_precision": 7,
        "layer_difference": 12,
        "corner_threshold": 60,
        "length_threshold": 2.0,
        "max_iterations": 15,
        "splice_threshold": 45,
        "path_precision": 6,
    },
    "ultra": {
        "colormode": "color",
        "hierarchical": "stacked",
        "mode": "spline",
        "filter_speckle": 0,
        "color_precision": 8,
        "layer_difference": 6,
        "corner_threshold": 60,
        "length_threshold": 1.5,
        "max_iterations": 20,
        "splice_threshold": 45,
        "path_precision": 8,
    },
}


class VTracerEngine(AbstractTracer):
    """VTracer-based color vectorization engine with junction-preserving supersampling."""

    @property
    def name(self) -> str:
        return "VTracer"

    @property
    def supports_color(self) -> bool:
        return True

    def trace(self, image_path: Path, output_svg_path: Path, params: dict) -> dict:
        try:
            preset_name = params.get("quality_preset", "balanced")
            preset = QUALITY_PRESETS.get(preset_name, QUALITY_PRESETS["balanced"]).copy()

            colormode = "color"
            hierarchical = params.get("hierarchical") or preset.get("hierarchical", "stacked")
            mode = self._get_mode(params)
            filter_speckle = int(params.get("filter_speckle", preset["filter_speckle"]))
            color_precision = int(params.get("color_precision", preset["color_precision"]))
            layer_difference = int(params.get("layer_difference", preset["layer_difference"]))
            corner_threshold = int(params.get("corner_threshold", preset["corner_threshold"]))
            length_threshold = float(params.get("length_threshold", preset["length_threshold"]))
            max_iterations = int(params.get("max_iterations", preset["max_iterations"]))
            splice_threshold = int(params.get("splice_threshold", preset["splice_threshold"]))
            path_precision = int(preset.get("path_precision", 5))

            # Fine line detail preservation via supersampling (no corner dilation)
            trace_image_path = image_path
            temp_enhanced_path = None
            preserve_fine_lines = params.get("preserve_fine_lines", True)
            used_scale = 1
            orig_img = cv2.imread(str(image_path), cv2.IMREAD_UNCHANGED)
            orig_h, orig_w = orig_img.shape[:2] if orig_img is not None else (300, 300)

            if preserve_fine_lines:
                temp_enhanced_path = image_path.parent / f"{image_path.stem}_fine_enhanced.png"
                enhanced_path, was_enhanced = enhance_fine_lines(image_path, temp_enhanced_path, scale=2)
                if was_enhanced:
                    trace_image_path = enhanced_path
                    hierarchical = "cutout"
                    filter_speckle = min(filter_speckle, 1)
                    length_threshold = min(length_threshold, 2.0)
                    used_scale = 2
                    logger.info(f"VTracer fine line mode active for {image_path.name}")

            logger.info(f"VTracer tracing {trace_image_path} -> {output_svg_path}")

            vtracer.convert_image_to_svg_py(
                str(trace_image_path),
                str(output_svg_path),
                colormode,
                hierarchical,
                mode,
                filter_speckle,
                color_precision,
                layer_difference,
                corner_threshold,
                length_threshold,
                max_iterations,
                splice_threshold,
                path_precision,
            )

            # Cleanup temp enhanced image
            if temp_enhanced_path and temp_enhanced_path.exists():
                try:
                    temp_enhanced_path.unlink()
                except Exception:
                    pass

            if used_scale > 1 and output_svg_path.exists():
                svg_content = output_svg_path.read_text(encoding="utf-8")
                import re

                def fix_root(m):
                    tag = m.group(0)
                    tag = re.sub(r'\s+width="[^"]*"', '', tag)
                    tag = re.sub(r'\s+height="[^"]*"', '', tag)
                    tag = re.sub(r'\s+viewBox="[^"]*"', '', tag)
                    return f'{tag[:-1]} width="{orig_w}" height="{orig_h}" viewBox="0 0 {orig_w * used_scale} {orig_h * used_scale}">'

                svg_content = re.sub(r'<svg\b[^>]*>', fix_root, svg_content, count=1)
                output_svg_path.write_text(svg_content, encoding="utf-8")

            svg_size = output_svg_path.stat().st_size if output_svg_path.exists() else 0
            logger.info(f"VTracer wrote SVG: {output_svg_path} ({svg_size} bytes)")

            return {
                "success": True,
                "engine": self.name,
                "error": None,
                "svg_size": svg_size,
            }

        except Exception as e:
            logger.error(f"VTracer failed: {e}", exc_info=True)
            return {
                "success": False,
                "engine": self.name,
                "error": str(e),
                "svg_size": 0,
            }

    def trace_bw(self, image_path: Path, output_svg_path: Path, params: dict) -> dict:
        """
        Trace as B&W/line art using 2x supersampling and binary cutout hierarchy.
        Preserves thin concentric circles, crosshairs, and fine lines with 100% integrity,
        preventing intersection webbing and line severance.
        """
        try:
            preset_name = params.get("quality_preset", "balanced")
            preset = QUALITY_PRESETS.get(preset_name, QUALITY_PRESETS["balanced"]).copy()

            orig_img = cv2.imread(str(image_path), cv2.IMREAD_UNCHANGED)
            orig_h, orig_w = orig_img.shape[:2] if orig_img is not None else (300, 300)
            has_alpha = orig_img is not None and len(orig_img.shape) == 3 and orig_img.shape[2] == 4

            # Fine line detail preservation
            trace_image_path = image_path
            temp_enhanced_path = image_path.parent / f"{image_path.stem}_fine_enhanced_bw.png"
            scale_factor = 4 if max(orig_h, orig_w) <= 1500 else 2
            enhanced_path, was_enhanced = enhance_fine_lines(image_path, temp_enhanced_path, scale=scale_factor)

            mode = self._get_mode(params)

            if was_enhanced:
                trace_image_path = enhanced_path
                colormode = "binary"
                hierarchical = "cutout"
                filter_speckle = 0
                length_threshold = float(params.get("length_threshold", 9.0))
                used_scale = scale_factor
            else:
                colormode = "color"
                hierarchical = "cutout"
                filter_speckle = int(params.get("filter_speckle", 0))
                length_threshold = float(params.get("length_threshold", preset["length_threshold"]))
                used_scale = 1

            color_precision = 2
            layer_difference = 16
            corner_threshold = int(params.get("corner_threshold", 75))
            max_iterations = int(params.get("max_iterations", preset["max_iterations"]))
            splice_threshold = int(params.get("splice_threshold", preset["splice_threshold"]))
            path_precision = int(preset.get("path_precision", 6))

            logger.info(f"VTracer BW tracing {trace_image_path} -> {output_svg_path} (colormode={colormode}, scale={used_scale})")

            vtracer.convert_image_to_svg_py(
                str(trace_image_path),
                str(output_svg_path),
                colormode,
                hierarchical,
                mode,
                filter_speckle,
                color_precision,
                layer_difference,
                corner_threshold,
                length_threshold,
                max_iterations,
                splice_threshold,
                path_precision,
            )

            # Cleanup temp enhanced image
            if temp_enhanced_path and temp_enhanced_path.exists():
                try:
                    temp_enhanced_path.unlink()
                except Exception:
                    pass

            if output_svg_path.exists():
                svg_content = output_svg_path.read_text(encoding="utf-8")
                import re

                def fix_root(m):
                    tag = m.group(0)
                    tag = re.sub(r'\s+width="[^"]*"', '', tag)
                    tag = re.sub(r'\s+height="[^"]*"', '', tag)
                    tag = re.sub(r'\s+viewBox="[^"]*"', '', tag)
                    bg_rect = '\n<rect width="100%" height="100%" fill="#ffffff"/>' if not has_alpha else ''
                    return f'{tag[:-1]} width="{orig_w}" height="{orig_h}" viewBox="0 0 {orig_w * used_scale} {orig_h * used_scale}">{bg_rect}'

                svg_content = re.sub(r'<svg\b[^>]*>', fix_root, svg_content, count=1)
                output_svg_path.write_text(svg_content, encoding="utf-8")

            svg_size = output_svg_path.stat().st_size if output_svg_path.exists() else 0
            return {"success": True, "engine": f"{self.name}/BW", "error": None, "svg_size": svg_size}

        except Exception as e:
            logger.error(f"VTracer BW failed: {e}", exc_info=True)
            return {"success": False, "engine": self.name, "error": str(e), "svg_size": 0}

    def _get_mode(self, params: dict) -> str:
        curve_fitting = params.get("curve_fitting", "spline")
        mapping = {
            "spline": "spline",
            "polygon": "polygon",
            "pixel": "pixel",
            "none": "polygon",
        }
        return mapping.get(curve_fitting, "spline")
