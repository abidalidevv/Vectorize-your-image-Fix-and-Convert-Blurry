"""
VectorForge AI — VTracer Engine
Primary color and line-art vectorization using the vtracer library (Rust-based).
Features fine line detail preservation and cutout hierarchy.
"""
import logging
from pathlib import Path
from typing import Any

import vtracer

from vectorization.base import AbstractTracer
from image_processing.line_detector import enhance_fine_lines, detect_line_art

logger = logging.getLogger(__name__)


# Quality preset → vtracer parameter mappings
QUALITY_PRESETS = {
    "fast": {
        "colormode": "color",
        "hierarchical": "cutout",
        "mode": "polygon",
        "filter_speckle": 4,
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
        "hierarchical": "cutout",
        "mode": "spline",
        "filter_speckle": 2,
        "color_precision": 6,
        "layer_difference": 16,
        "corner_threshold": 60,
        "length_threshold": 3.0,
        "max_iterations": 10,
        "splice_threshold": 45,
        "path_precision": 5,
    },
    "high": {
        "colormode": "color",
        "hierarchical": "cutout",
        "mode": "spline",
        "filter_speckle": 1,
        "color_precision": 8,
        "layer_difference": 8,
        "corner_threshold": 60,
        "length_threshold": 2.0,
        "max_iterations": 15,
        "splice_threshold": 45,
        "path_precision": 8,
    },
    "ultra": {
        "colormode": "color",
        "hierarchical": "cutout",
        "mode": "spline",
        "filter_speckle": 0,
        "color_precision": 8,
        "layer_difference": 4,
        "corner_threshold": 60,
        "length_threshold": 1.0,
        "max_iterations": 20,
        "splice_threshold": 45,
        "path_precision": 10,
    },
}


class VTracerEngine(AbstractTracer):
    """VTracer-based color vectorization engine with fine-line preservation."""

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
            hierarchical = params.get("hierarchical", "cutout")
            mode = self._get_mode(params)
            filter_speckle = int(params.get("filter_speckle", preset["filter_speckle"]))
            color_precision = int(params.get("color_precision", preset["color_precision"]))
            layer_difference = int(params.get("layer_difference", preset["layer_difference"]))
            corner_threshold = int(params.get("corner_threshold", preset["corner_threshold"]))
            length_threshold = float(params.get("length_threshold", preset["length_threshold"]))
            max_iterations = int(params.get("max_iterations", preset["max_iterations"]))
            splice_threshold = int(params.get("splice_threshold", preset["splice_threshold"]))
            path_precision = int(preset.get("path_precision", 5))

            # Fine line detail preservation
            trace_image_path = image_path
            temp_enhanced_path = None
            preserve_fine_lines = params.get("preserve_fine_lines", True)

            if preserve_fine_lines:
                temp_enhanced_path = image_path.parent / f"{image_path.stem}_fine_enhanced.png"
                enhanced_path, was_enhanced = enhance_fine_lines(image_path, temp_enhanced_path)
                if was_enhanced:
                    trace_image_path = enhanced_path
                    hierarchical = "cutout"
                    filter_speckle = min(filter_speckle, 1)
                    length_threshold = min(length_threshold, 2.0)
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

            # Cleanup temp enhanced image if created
            if temp_enhanced_path and temp_enhanced_path.exists():
                try:
                    temp_enhanced_path.unlink()
                except Exception:
                    pass

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
        Trace as B&W/line art using fine-line preservation and cutout hierarchy.
        Avoids VTracer binary mode polygon inversion bug by using 2-level color cutout.
        """
        try:
            preset_name = params.get("quality_preset", "balanced")
            preset = QUALITY_PRESETS.get(preset_name, QUALITY_PRESETS["balanced"]).copy()

            colormode = "color"
            hierarchical = "cutout"
            mode = self._get_mode(params)

            # Fine line detail preservation
            trace_image_path = image_path
            temp_enhanced_path = image_path.parent / f"{image_path.stem}_fine_enhanced_bw.png"
            enhanced_path, was_enhanced = enhance_fine_lines(image_path, temp_enhanced_path)
            if was_enhanced:
                trace_image_path = enhanced_path
                filter_speckle = 0
                length_threshold = min(float(params.get("length_threshold", 2.0)), 2.0)
            else:
                filter_speckle = int(params.get("filter_speckle", 0))
                length_threshold = float(params.get("length_threshold", preset["length_threshold"]))

            color_precision = 2
            layer_difference = 16
            corner_threshold = int(params.get("corner_threshold", preset["corner_threshold"]))
            max_iterations = int(params.get("max_iterations", preset["max_iterations"]))
            splice_threshold = int(params.get("splice_threshold", preset["splice_threshold"]))
            path_precision = int(preset.get("path_precision", 6))

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
