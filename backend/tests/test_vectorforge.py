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


def test_fine_line_and_concentric_circles_preservation():
    """Verify that thin 1-pixel concentric circles in test_bw.png are 100% preserved."""
    import resvg_py
    import cv2
    import numpy as np
    from vectorization.engine_selector import select_and_trace

    bw_path = SAMPLES_DIR / "test_bw.png"
    out_svg = TMP_DIR / "test_bw_vectorized.svg"

    # Test auto mode (should auto-detect line art and preserve fine rings)
    result = select_and_trace(bw_path, out_svg, {"image_mode": "auto"})
    assert result["success"] is True
    assert out_svg.exists()

    # Render vector to raster to verify visual presence of all concentric rings
    svg_content = out_svg.read_text(encoding="utf-8")
    png_bytes = resvg_py.svg_to_bytes(svg_content)
    r_img = cv2.imdecode(np.frombuffer(png_bytes, np.uint8), cv2.IMREAD_GRAYSCALE)

    # Calculate radii of dark pixels from center (150, 150), excluding crosshair
    ys, xs = np.where(r_img < 100)
    radii = np.sqrt((xs - 150) ** 2 + (ys - 150) ** 2)
    mask = (np.abs(xs - 150) > 3) & (np.abs(ys - 150) > 3)
    circle_radii = radii[mask]

    counts, bin_edges = np.histogram(circle_radii, bins=range(0, 150, 2))
    detected_circles = {}
    for r, c in zip(bin_edges, counts):
        if c > 20:
            detected_circles[int(r)] = int(c)

    # Verify that all 4 inner concentric circles + outer circle exist:
    # 1. Circle around r=24
    assert any(20 <= r <= 28 for r in detected_circles), "Innermost circle (r~24) missing!"
    # 2. Circle around r=48-50
    assert any(46 <= r <= 54 for r in detected_circles), "Second circle (r~50) missing!"
    # 3. Circle around r=74
    assert any(70 <= r <= 78 for r in detected_circles), "Third circle (r~74) missing!"
    # 4. Circle around r=98-100
    assert any(94 <= r <= 104 for r in detected_circles), "Fourth circle (r~100) missing!"
    # 5. Outer circle around r=126-130
    assert any(122 <= r <= 132 for r in detected_circles), "Outer circle (r~128) missing!"

    # 6. Verify 4-quadrant symmetry: ensure no quadrant has missing arcs or thick black wedges
    q1 = np.sum(r_img[0:150, 150:300] < 128)
    q2 = np.sum(r_img[0:150, 0:150] < 128)
    q3 = np.sum(r_img[150:300, 0:150] < 128)
    q4 = np.sum(r_img[150:300, 150:300] < 128)
    mean_q = (q1 + q2 + q3 + q4) / 4.0
    for i, q in enumerate([q1, q2, q3, q4], 1):
        assert abs(q - mean_q) / mean_q < 0.20, f"Quadrant Q{i} has asymmetric pixel count ({q} vs mean {mean_q:.1f}) indicating distortion/wedging!"


def test_color_vectorization_circle_and_junction_integrity():
    """Verify that color vectorization (test_complex.png) has 0 seam holes, smooth circle, and no black wedges."""
    import resvg_py
    import cv2
    import numpy as np
    from vectorization.engine_selector import select_and_trace

    complex_path = SAMPLES_DIR / "test_complex.png"
    out_svg = TMP_DIR / "test_complex_vectorized.svg"

    # Trace with default parameters
    result = select_and_trace(complex_path, out_svg, {
        "image_mode": "auto",
        "quality_preset": "high",
    })
    assert result["success"] is True
    assert out_svg.exists()

    # Render vector to RGBA to inspect integrity
    svg_content = out_svg.read_text(encoding="utf-8")
    png_bytes = resvg_py.svg_to_bytes(svg_content)
    rendered = cv2.imdecode(np.frombuffer(png_bytes, np.uint8), cv2.IMREAD_UNCHANGED)

    # 1. Verify ZERO transparent seam gaps / holes
    if rendered.shape[-1] == 4:
        holes = int(np.count_nonzero(rendered[:, :, 3] < 250))
        assert holes == 0, f"Expected 0 transparent seam holes, found {holes}!"

    # 2. Verify blue circle integrity (smooth circle with no notches or dents)
    blue_mask = ((rendered[:, :, 0] > 180) & (rendered[:, :, 2] < 100)).astype(np.uint8) * 255
    cnts, _ = cv2.findContours(blue_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    assert len(cnts) > 0, "Blue circle must be detected!"
    c = max(cnts, key=cv2.contourArea)
    (cx, cy), r = cv2.minEnclosingCircle(c)
    pts = c.reshape(-1, 2)
    dists = np.sqrt((pts[:, 0] - cx) ** 2 + (pts[:, 1] - cy) ** 2)
    r_diff = float(np.max(np.abs(dists - r)))
    assert r_diff < 2.0, f"Circle perimeter deviation too high: {r_diff:.2f}px (stepped notch/dent)!"

    # 3. Verify junction integrity (no black wedges/triangles at crossing)
    # Crossing region: x=130..180, y=235..270
    crossing_crop = rendered[235:270, 130:180]
    dark_crossing = np.count_nonzero(
        (crossing_crop[:, :, 0] < 30) & (crossing_crop[:, :, 1] < 30) & (crossing_crop[:, :, 2] < 30)
    )
    assert dark_crossing == 0, f"Found {dark_crossing} black wedge pixels at line crossing!"

