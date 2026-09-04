"""
VectorForge AI — VTracer Engine
Primary color vectorization using the vtracer library (Rust-based).
"""
import logging
from pathlib import Path
from typing import Any

import vtracer

from vectorization.base import AbstractTracer

logger = logging.getLogger(__name__)


# Quality preset → vtracer parameter mappings
QUALITY_PRESETS = {
    "fast": {
        "colormode": "color",
        "hierarchical": "stacked",
        "mode": "polygon",
        "filter_speckle": 8,
        "color_precision": 4,
        "layer_difference": 24,
        "corner_threshold": 60,
        "length_threshold": 6.0,
        "max_iterations": 5,
        "splice_threshold": 45,
        "path_precision": 3,
    },
    "balanced": {
        "colormode": "color",
        "hierarchical": "stacked",
        "mode": "spline",
        "filter_speckle": 4,
        "color_precision": 6,
        "layer_difference": 16,
        "corner_threshold": 60,
        "length_threshold": 4.0,
        "max_iterations": 10,
        "splice_threshold": 45,
        "path_precision": 5,
    },
    "high": {
        "colormode": "color",
        "hierarchical": "stacked",
        "mode": "spline",
        "filter_speckle": 2,
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
        "hierarchical": "stacked",
        "mode": "spline",
        "filter_speckle": 1,
        "color_precision": 8,
        "layer_difference": 4,
        "corner_threshold": 60,
        "length_threshold": 1.5,
        "max_iterations": 20,
        "splice_threshold": 45,
        "path_precision": 10,
    },
}


class VTracerEngine(AbstractTracer):
    """VTracer-based color vectorization engine."""

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
            hierarchical = "stacked"
            mode = self._get_mode(params)
            filter_speckle = int(params.get("filter_speckle", preset["filter_speckle"]))
            color_precision = int(params.get("color_precision", preset["color_precision"]))
            layer_difference = int(params.get("layer_difference", preset["layer_difference"]))
            corner_threshold = int(params.get("corner_threshold", preset["corner_threshold"]))
            length_threshold = float(params.get("length_threshold", preset["length_threshold"]))
            max_iterations = int(params.get("max_iterations", preset["max_iterations"]))
            splice_threshold = int(params.get("splice_threshold", preset["splice_threshold"]))
            path_precision = int(preset.get("path_precision", 5))

            logger.info(f"VTracer tracing {image_path} -> {output_svg_path}")

            vtracer.convert_image_to_svg_py(
                str(image_path),
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
        """Trace as binary (B&W) using VTracer's binary color mode."""
        try:
            preset_name = params.get("quality_preset", "balanced")
            preset = QUALITY_PRESETS.get(preset_name, QUALITY_PRESETS["balanced"]).copy()

            colormode = "binary"
            hierarchical = "stacked"
            mode = self._get_mode(params)
            filter_speckle = int(params.get("filter_speckle", preset["filter_speckle"]))
            color_precision = 1
            layer_difference = 16
            corner_threshold = int(params.get("corner_threshold", preset["corner_threshold"]))
            length_threshold = float(params.get("length_threshold", preset["length_threshold"]))
            max_iterations = int(params.get("max_iterations", preset["max_iterations"]))
            splice_threshold = int(params.get("splice_threshold", preset["splice_threshold"]))
            path_precision = int(preset.get("path_precision", 5))

            vtracer.convert_image_to_svg_py(
                str(image_path),
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
