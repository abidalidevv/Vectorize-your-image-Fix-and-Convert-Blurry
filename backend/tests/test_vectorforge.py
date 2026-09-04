"""
VectorForge AI — Comprehensive Test Suite
"""
import sys
from pathlib import Path
import pytest

# Ensure app is in path
APP_DIR = Path(__file__).resolve().parent.parent / "app"
sys.path.insert(0, str(APP_DIR))

from image_processing.analyzer import analyze_image
from image_processing.preprocessor import apply_preprocessing
from image_processing.quantizer import quantize_image
from vectorization.vtracer_engine import VTracerEngine
from vectorization.contour_engine import ContourEngine
from utils.svg_optimizer import validate_svg, optimize_svg, ensure_viewbox, extract_layers_from_svg
from export.svg_exporter import export_svg
from export.png_exporter import export_png

SAMPLES_DIR = Path(__file__).resolve().parent.parent.parent / "samples"
TMP_DIR = APP_DIR / "temp_files" / "test_scratch"
TMP_DIR.mkdir(parents=True, exist_ok=True)


def test_analyzer_logo():
    logo_path = SAMPLES_DIR / "test_logo.png"
    assert logo_path.exists()
    result = analyze_image(logo_path)
    assert result["recommended_mode"] in ("logo", "clipart", "illustration")
    assert result["confidence"] >= 0.5
    assert result["color_count_estimate"] > 0
    assert len(result["dominant_colors"]) > 0
    assert isinstance(result["dominant_colors"][0]["percentage"], float)


def test_analyzer_bw():
    bw_path = SAMPLES_DIR / "test_bw.png"
    assert bw_path.exists()
    result = analyze_image(bw_path)
    assert result["is_grayscale"] is True
    assert result["recommended_mode"] in ("bw", "sketch")


def test_preprocessor_pipeline():
    in_path = SAMPLES_DIR / "test_logo.png"
    out_path = TMP_DIR / "preprocessed.png"
    applied = apply_preprocessing(
        in_path,
        {
            "denoise_enabled": True,
            "denoise_strength": 2.0,
            "contrast": 1.2,
            "brightness": 1.05,
        },
        out_path,
    )
    assert out_path.exists()
    assert len(applied) > 0


def test_quantizer_kmeans():
    in_path = SAMPLES_DIR / "test_logo.png"
    out_path = TMP_DIR / "quantized_kmeans.png"
    result = quantize_image(in_path, out_path, num_colors=6, method="kmeans")
    assert out_path.exists()
    assert result["actual_colors"] <= 6
    assert len(result["palette"]) == result["actual_colors"]
    for c in result["palette"]:
        assert c["hex"].startswith("#")
        assert len(c["rgb"]) == 3


def test_vtracer_color_tracing():
    in_path = SAMPLES_DIR / "test_logo.png"
    out_svg = TMP_DIR / "vtracer_output.svg"
    engine = VTracerEngine()
    result = engine.trace(in_path, out_svg, {"quality_preset": "balanced", "curve_fitting": "spline"})
    assert result["success"] is True
    assert out_svg.exists()
    assert out_svg.stat().st_size > 0

    content = out_svg.read_text(encoding="utf-8")
    validation = validate_svg(content)
    assert validation["valid"] is True
    assert validation["stats"]["path_count"] > 0
    assert not validation["stats"]["contains_raster"]


def test_contour_engine_bw():
    in_path = SAMPLES_DIR / "test_bw.png"
    out_svg = TMP_DIR / "contour_output.svg"
    engine = ContourEngine()
    result = engine.trace(in_path, out_svg, {"min_area": 5.0})
    assert result["success"] is True
    assert out_svg.exists()
    content = out_svg.read_text(encoding="utf-8")
    assert "<svg" in content
    assert "<path" in content


def test_svg_viewbox_and_optimization():
    svg_raw = '<svg width="200" height="150"><path d="M 0 0 L 200 150" fill="#ff0000"/></svg>'
    fixed = ensure_viewbox(svg_raw)
    assert 'viewBox="0 0 200 150"' in fixed

    optimized = optimize_svg(fixed)
    assert "<svg" in optimized
    assert "200" in optimized


def test_layer_extraction():
    svg_test = '<svg viewBox="0 0 100 100"><path fill="#ff0000" d="M0 0 h10"/><path fill="#00ff00" d="M10 10 h10"/></svg>'
    layers = extract_layers_from_svg(svg_test)
    assert len(layers) == 2
    assert any(l["color_hex"].lower() == "#ff0000" for l in layers)
    assert any(l["color_hex"].lower() == "#00ff00" for l in layers)


def test_export_svg_and_png():
    in_path = SAMPLES_DIR / "test_logo.png"
    svg_path = TMP_DIR / "export_test.svg"
    png_path = TMP_DIR / "export_test.png"

    # Vectorize first
    engine = VTracerEngine()
    engine.trace(in_path, svg_path, {"quality_preset": "balanced"})

    # Export SVG
    opt_svg = TMP_DIR / "export_opt.svg"
    svg_res = export_svg(svg_path, opt_svg, optimize=True)
    assert opt_svg.exists()
    assert svg_res["file_size_bytes"] > 0

    # Export PNG
    png_res = export_png(svg_path, png_path, scale=2)
    assert png_path.exists()
    assert png_res["renderer"] == "resvg"
    assert png_path.stat().st_size > 0
