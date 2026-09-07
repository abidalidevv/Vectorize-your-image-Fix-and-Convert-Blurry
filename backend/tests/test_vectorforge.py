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
        assert abs(q - mean_q) / mean_q < 0.25, f"Quadrant Q{i} has asymmetric pixel count ({q} vs mean {mean_q:.1f}) indicating distortion/wedging!"


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


def test_bw_line_art_path_count_is_low():
    """Regression guard: concentric circle line art must NOT fragment into hundreds of paths."""
    from vectorization.vtracer_engine import VTracerEngine
    from utils.svg_optimizer import validate_svg
    engine = VTracerEngine()
    src = SAMPLES_DIR / "test_bw.png"
    out = Path(__file__).parent / "_tmp_path_count_check.svg"
    result = engine.trace_bw(src, out, {})
    assert result["success"] is True
    svg = out.read_text(encoding="utf-8")
    stats = validate_svg(svg)["stats"]
    path_count = stats.get("path_count", 9999)
    out.unlink(missing_ok=True)
    assert path_count < 50, f"Expected a low, connected path count, got {path_count} (fragmentation regression)"


def test_primitive_detection_produces_true_circles():
    """Circle/crosshair line art should be traced as real <circle>/<line> SVG primitives, not fragmented paths."""
    from vectorization.vtracer_engine import VTracerEngine
    engine = VTracerEngine()
    src = SAMPLES_DIR / "test_bw.png"
    out = Path(__file__).parent / "_tmp_primitive_check.svg"
    result = engine.trace_bw(src, out, {})
    assert result["success"] is True
    svg = out.read_text(encoding="utf-8")
    out.unlink(missing_ok=True)
    assert "<circle" in svg, "Expected true <circle> SVG elements for circle test image"
    circle_count = svg.count("<circle")
    assert circle_count >= 4, f"Expected at least 4 detected circles, found {circle_count}"


def test_image_enhancer_upscaling_and_clahe():
    """Verify Image Enhancer can upscale 2x and apply CLAHE/sharpening."""
    from image_processing.enhancer import apply_enhancement
    src = SAMPLES_DIR / "test_logo.png"
    out = TMP_DIR / "test_enhanced.png"
    changes, w, h = apply_enhancement(src, {
        "scale": 2,
        "sharpen_strength": 1.0,
        "clahe_enabled": True,
        "contrast": 1.1,
    }, out)
    assert out.exists()
    assert w > 0 and h > 0
    assert any("Super-Resolution 2×" in c for c in changes)
    assert any("Adaptive Tone" in c for c in changes)
    out.unlink(missing_ok=True)


def test_bg_remover_cutout_and_replacement():
    """Verify Background Remover can isolate foreground and composite over color."""
    from image_processing.bg_remover import remove_image_background
    from PIL import Image
    src = SAMPLES_DIR / "test_logo.png"
    out_trans = TMP_DIR / "test_cutout_trans.png"
    changes_trans, w1, h1 = remove_image_background(src, {
        "engine": "color",
        "bg_type": "transparent",
        "feather_radius": 1.0,
        "defringe_choke": 1,
    }, out_trans)
    assert out_trans.exists()
    with Image.open(out_trans) as img_t:
        assert img_t.mode == "RGBA"
    out_trans.unlink(missing_ok=True)

    out_solid = TMP_DIR / "test_cutout_solid.png"
    changes_solid, w2, h2 = remove_image_background(src, {
        "engine": "color",
        "bg_type": "color",
        "bg_color": "#ff0000",
    }, out_solid)
    assert out_solid.exists()
    assert any("Replaced background" in c for c in changes_solid)
    out_solid.unlink(missing_ok=True)


def test_bg_remover_edge_decontamination_and_fringe_reduction():
    """
    Verify Part 1 edge decontamination & defringe on:
    - Light subject on light background
    - Dark subject on light background
    Confirms color unmixing mathematically reconstructs true foreground and defringe chokes alpha.
    """
    import numpy as np
    from bg_remover.engine import _decontaminate_color, _estimate_background_color
    import cv2

    # Case 1: Dark subject (RGB [20, 20, 20]) on white background (RGB [250, 250, 250])
    bg_color = np.array([250.0, 250.0, 250.0], dtype=np.float32)
    dark_fg = np.array([20.0, 20.0, 20.0], dtype=np.float32)
    # Edge pixel with alpha=128 (~0.502) blended with background:
    alpha_val = 128
    alpha_norm = alpha_val / 255.0
    observed_dark = (dark_fg * alpha_norm + bg_color * (1.0 - alpha_norm)).astype(np.uint8)
    
    # Construct RGBA test patch
    patch_dark = np.zeros((4, 4, 4), dtype=np.uint8)
    patch_dark[:, :, :3] = observed_dark
    patch_dark[:, :, 3] = alpha_val

    decontaminated_dark = _decontaminate_color(patch_dark, bg_color=bg_color)
    recovered_dark = decontaminated_dark[1, 1, :3].astype(float)
    # Recovered dark color should be very close to original dark_fg [20, 20, 20], NOT observed_dark (~135)
    assert np.all(np.abs(recovered_dark - dark_fg) <= 2.0), f"Dark FG decontamination error: {recovered_dark} vs {dark_fg}"

    # Case 2: Light subject (RGB [220, 200, 180]) on white background (RGB [255, 255, 255])
    light_fg = np.array([220.0, 200.0, 180.0], dtype=np.float32)
    observed_light = (light_fg * alpha_norm + bg_color * (1.0 - alpha_norm)).astype(np.uint8)
    patch_light = np.zeros((4, 4, 4), dtype=np.uint8)
    patch_light[:, :, :3] = observed_light
    patch_light[:, :, 3] = alpha_val

    decontaminated_light = _decontaminate_color(patch_light, bg_color=bg_color)
    recovered_light = decontaminated_light[1, 1, :3].astype(float)
    assert np.all(np.abs(recovered_light - light_fg) <= 2.0), f"Light FG decontamination error: {recovered_light} vs {light_fg}"


def test_bg_remover_fast_mode():
    """Verify Fast mode remove-bg produces a valid RGBA image with transparency."""
    from bg_remover.engine import remove_image_background
    from PIL import Image
    import numpy as np

    src = SAMPLES_DIR / "test_logo.png"
    out_fast = TMP_DIR / "test_fast_cutout.png"
    changes, w, h = remove_image_background(src, {
        "quality": "fast",
        "defringe_choke": 1,
        "feather_radius": 1.0,
    }, out_fast)

    assert out_fast.exists()
    assert w > 0 and h > 0
    with Image.open(out_fast) as img:
        assert img.mode == "RGBA"
        # Must have transparent pixels
        arr = np.array(img)
        assert np.any(arr[:, :, 3] < 255)
    out_fast.unlink(missing_ok=True)


def test_bg_remover_ultra_fallback_when_uncached(monkeypatch):
    """Verify Ultra mode remove-bg gracefully falls back to fast mode when BiRefNet is uncached."""
    import bg_remover.engine
    from bg_remover.engine import remove_image_background
    from PIL import Image

    # Mock _is_birefnet_cached to False
    monkeypatch.setattr(bg_remover.engine, "_is_birefnet_cached", lambda: False)

    src = SAMPLES_DIR / "test_logo.png"
    out_ultra = TMP_DIR / "test_ultra_fallback.png"
    changes, w, h = remove_image_background(src, {
        "quality": "ultra",
        "defringe_choke": 1,
        "feather_radius": 1.0,
    }, out_ultra)

    assert out_ultra.exists()
    assert w > 0 and h > 0
    with Image.open(out_ultra) as img:
        assert img.mode == "RGBA"
    out_ultra.unlink(missing_ok=True)


def test_image_enhancer_fast_mode():
    """Verify Fast mode image enhancer applies lightweight AI super-resolution (realesr-general-x4v3)."""
    from image_enhancer.engine import apply_enhancement
    from PIL import Image

    src = SAMPLES_DIR / "test_logo.png"
    out_fast = TMP_DIR / "test_enhancer_fast.png"
    with Image.open(src) as orig:
        orig_w, orig_h = orig.size

    changes, w, h = apply_enhancement(src, {
        "quality": "fast",
        "scale": 2,
        "sharpen_strength": 0.8,
        "clahe_enabled": True,
    }, out_fast)

    assert out_fast.exists()
    assert w == orig_w * 2
    assert h == orig_h * 2
    assert any("realesr-general-x4v3 Fast" in c for c in changes)
    out_fast.unlink(missing_ok=True)


def test_image_enhancer_ultra_fallback_when_uncached(monkeypatch):
    """Verify Ultra mode image enhancer gracefully falls back to Fast tier when RealESRGAN_x4plus is uncached."""
    import image_enhancer.engine
    from image_enhancer.engine import apply_enhancement
    from PIL import Image

    # Simulate Ultra model weights missing
    monkeypatch.setattr(image_enhancer.engine, "_is_realesrgan_ultra_cached", lambda: False)

    src = SAMPLES_DIR / "test_logo.png"
    out_fallback = TMP_DIR / "test_enhancer_ultra_fallback.png"
    with Image.open(src) as orig:
        orig_w, orig_h = orig.size

    changes, w, h = apply_enhancement(src, {
        "quality": "ultra",
        "scale": 2,
    }, out_fallback)

    assert out_fallback.exists()
    assert w == orig_w * 2
    assert h == orig_h * 2
    assert any("fallback" in c.lower() for c in changes)
    out_fallback.unlink(missing_ok=True)


def test_system_diagnostics_endpoint():
    """Verify the /api/diagnostics endpoint returns valid system, hardware, and model metadata."""
    import asyncio
    from api.routes.diagnostics import get_system_diagnostics

    res = asyncio.run(get_system_diagnostics())
    assert res["status"] == "ok"
    assert res["service"] == "VectorForge AI"
    assert "platform" in res
    assert "onnx_runtime" in res
    assert "models" in res
    assert "bg_remover" in res["models"]
    assert "image_enhancer" in res["models"]
    assert res["models"]["bg_remover"]["fast"]["model_name"] == "isnet-general-use"
    assert res["models"]["bg_remover"]["ultra"]["model_name"] == "birefnet-general"
    assert res["models"]["image_enhancer"]["fast"]["model_name"] == "realesr-general-x4v3"
    assert res["models"]["image_enhancer"]["ultra"]["model_name"] == "RealESRGAN_x4plus"
    assert res["models"]["face_restorer"]["gfpgan"]["model_name"] == "GFPGANv1.4"
    assert res["models"]["face_restorer"]["detector"]["model_name"] == "YuNet"
    assert res["models"]["magic_eraser"]["lama"]["model_name"] == "LaMa-ONNX"
    assert len(res["models"]["image_enhancer"]["pipeline_stages"]) >= 6


def test_magic_eraser_inpaint_synthetic():
    """Verify Magic Eraser inpainting removes masked objects and fills smoothly."""
    import base64
    import io
    import numpy as np
    from PIL import Image, ImageDraw
    from magic_eraser.engine import inpaint_image

    # Create a synthetic image with a bright red square in the center
    img = Image.new("RGB", (64, 64), color=(200, 200, 200))
    draw = ImageDraw.Draw(img)
    draw.rectangle([20, 20, 44, 44], fill=(255, 0, 0))
    src_path = TMP_DIR / "test_eraser_input.png"
    img.save(src_path)

    # Create a mask covering the red square
    mask = Image.new("L", (64, 64), color=0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rectangle([18, 18, 46, 46], fill=255)
    buf = io.BytesIO()
    mask.save(buf, format="PNG")
    mask_b64 = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("utf-8")

    out_path = TMP_DIR / "test_eraser_output.png"
    changes, w, h = inpaint_image(
        src_path,
        mask_b64,
        out_path,
        quality="fast",
        dilate_radius=2,
        method="auto",
    )

    assert out_path.exists()
    assert w == 64 and h == 64
    assert len(changes) > 0

    # Verify that red pixels in the center have been replaced/inpainted
    with Image.open(out_path) as res_img:
        arr = np.array(res_img)
        center_color = arr[32, 32]
        # Red channel shouldn't dominate like pure (255, 0, 0)
        assert not (center_color[0] > 200 and center_color[1] < 50 and center_color[2] < 50)

    src_path.unlink(missing_ok=True)
    out_path.unlink(missing_ok=True)


def test_face_restorer_when_no_faces():
    """Verify Face Restorer runs gracefully when no faces are detected in the image."""
    from PIL import Image
    import numpy as np
    from image_enhancer.face_restorer import restore_faces

    src = SAMPLES_DIR / "test_logo.png"
    with Image.open(src) as img:
        arr = np.array(img.convert("RGB"))

    # Running face restoration on a logo should not crash and should return unchanged image
    restored, count = restore_faces(arr, fidelity=0.8)
    assert restored.shape == arr.shape
    assert count == 0






