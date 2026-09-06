"""
VectorForge AI — Image Enhancer Studio Engine
Super-resolution upscaling via Real-ESRGAN (realesr-general-x4v3 ONNX), deblur,
sharpening, CLAHE adaptive tone, and color enhancement.

First-Run Model Pre-Download (Optional):
To avoid any network delay on the first live upscale request, pre-download the ~4.8MB
model once using:
    python -c "import urllib.request, pathlib; p = pathlib.Path.home() / '.cache' / 'realesrgan' / 'realesr-general-x4v3.onnx'; p.parent.mkdir(parents=True, exist_ok=True); urllib.request.urlretrieve('https://huggingface.co/Heliosoph/realesrgan-onnx/resolve/main/realesr-general-x4v3.onnx', str(p))"
"""
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional

import cv2
import numpy as np
from PIL import Image, ImageEnhance

logger = logging.getLogger(__name__)

MODEL_CACHE_DIR = Path.home() / ".cache" / "realesrgan"

# Fast tier: lightweight realesr-general-x4v3 ONNX (~4.8MB)
FAST_MODEL_URL = "https://huggingface.co/Heliosoph/realesrgan-onnx/resolve/main/realesr-general-x4v3.onnx"
FAST_MODEL_FILE = MODEL_CACHE_DIR / "realesr-general-x4v3.onnx"

# Ultra tier: full RealESRGAN_x4plus ONNX (~67MB, RRDBNet architecture)
ULTRA_MODEL_URL = "https://huggingface.co/anakhiu/realesrgan-onnx/resolve/main/realesrgan_x4plus.onnx"
ULTRA_MODEL_FILE = MODEL_CACHE_DIR / "RealESRGAN_x4plus.onnx"

_FAST_SESSION = None
_FAST_FAILED = False
_ULTRA_SESSION = None
_ULTRA_FAILED = False


def _get_fast_session():
    """Load and cache the Fast tier Real-ESRGAN (realesr-general-x4v3) ONNX session singleton."""
    global _FAST_SESSION, _FAST_FAILED
    if _FAST_SESSION is not None:
        return _FAST_SESSION
    if _FAST_FAILED:
        return None

    try:
        import onnxruntime as ort
        if not FAST_MODEL_FILE.exists() or FAST_MODEL_FILE.stat().st_size < 1_000_000:
            return None

        opts = ort.SessionOptions()
        opts.inter_op_num_threads = 2
        opts.intra_op_num_threads = 4
        _FAST_SESSION = ort.InferenceSession(
            str(FAST_MODEL_FILE),
            sess_options=opts,
            providers=['CPUExecutionProvider']
        )
        logger.info("Real-ESRGAN Fast (realesr-general-x4v3) session initialized.")
        return _FAST_SESSION
    except Exception as e:
        logger.warning(f"Fast Real-ESRGAN session initialization failed: {e}")
        _FAST_FAILED = True
        return None


def _get_ultra_session():
    """Load and cache the Ultra tier Real-ESRGAN (RealESRGAN_x4plus) ONNX session singleton."""
    global _ULTRA_SESSION, _ULTRA_FAILED
    if _ULTRA_SESSION is not None:
        return _ULTRA_SESSION
    if _ULTRA_FAILED:
        return None

    try:
        import onnxruntime as ort
        if not ULTRA_MODEL_FILE.exists() or ULTRA_MODEL_FILE.stat().st_size < 50_000_000:
            return None

        opts = ort.SessionOptions()
        opts.inter_op_num_threads = 2
        opts.intra_op_num_threads = 4
        _ULTRA_SESSION = ort.InferenceSession(
            str(ULTRA_MODEL_FILE),
            sess_options=opts,
            providers=['CPUExecutionProvider']
        )
        logger.info("Real-ESRGAN Ultra (RealESRGAN_x4plus) session initialized.")
        return _ULTRA_SESSION
    except Exception as e:
        logger.warning(f"Ultra Real-ESRGAN session initialization failed: {e}")
        _ULTRA_FAILED = True
        return None


def _get_realesrgan_session():
    """Backward compatibility helper defaulting to Fast tier session."""
    return _get_fast_session()


def _is_realesrgan_fast_cached() -> bool:
    """Check if the Fast tier model (realesr-general-x4v3.onnx) is cached locally."""
    return FAST_MODEL_FILE.exists() and FAST_MODEL_FILE.stat().st_size > 1_000_000


def _is_realesrgan_ultra_cached() -> bool:
    """Check if the Ultra tier model (RealESRGAN_x4plus.onnx, ~67MB) is cached locally."""
    return ULTRA_MODEL_FILE.exists() and ULTRA_MODEL_FILE.stat().st_size > 50_000_000


def _is_realesrgan_cached() -> bool:
    """Backward compatibility helper checking if any Real-ESRGAN weights are cached."""
    return _is_realesrgan_fast_cached()


def _run_tiled_realesrgan(sess, img_rgb: np.ndarray, tile_size: int = 256, tile_pad: int = 16) -> np.ndarray:
    """Run Real-ESRGAN inference with tiling support for memory safety on large images."""
    h, w, c = img_rgb.shape
    scale = 4

    # Run direct inference for small/medium images (up to tile_size)
    if max(h, w) <= tile_size:
        inp = (img_rgb.astype(np.float32) / 255.0).transpose(2, 0, 1)[np.newaxis, :]
        out = sess.run(None, {'input': inp})[0]
        return np.clip(out[0].transpose(1, 2, 0) * 255.0, 0, 255).astype(np.uint8)

    # Tiled inference for large images to avoid high memory spikes
    output = np.zeros((h * scale, w * scale, c), dtype=np.uint8)
    for y in range(0, h, tile_size):
        for x in range(0, w, tile_size):
            y_end = min(y + tile_size, h)
            x_end = min(x + tile_size, w)
            y_start_pad = max(0, y - tile_pad)
            x_start_pad = max(0, x - tile_pad)
            y_end_pad = min(h, y_end + tile_pad)
            x_end_pad = min(w, x_end + tile_pad)

            patch = img_rgb[y_start_pad:y_end_pad, x_start_pad:x_end_pad]
            inp = (patch.astype(np.float32) / 255.0).transpose(2, 0, 1)[np.newaxis, :]
            out_patch = sess.run(None, {'input': inp})[0]
            out_rgb = np.clip(out_patch[0].transpose(1, 2, 0) * 255.0, 0, 255).astype(np.uint8)

            crop_y1 = (y - y_start_pad) * scale
            crop_x1 = (x - x_start_pad) * scale
            crop_y2 = crop_y1 + (y_end - y) * scale
            crop_x2 = crop_x1 + (x_end - x) * scale

            output[y * scale:y_end * scale, x * scale:x_end * scale] = out_rgb[crop_y1:crop_y2, crop_x1:crop_x2]

    return output


def _upscale_image(np_rgb: np.ndarray, orig_w: int, orig_h: int, scale: int, quality: str = "fast") -> Tuple[np.ndarray, str]:
    """
    Upscale RGB image with tiered AI super-resolution:
    - Ultra mode: Full RealESRGAN_x4plus (RRDBNet, ~67MB) -> fallback to Fast mode
    - Fast mode (default): realesr-general-x4v3 (~4.8MB) -> fallback to Lanczos-4
    """
    target_w = orig_w * scale
    target_h = orig_h * scale

    # ── 1. Ultra Quality Tier (RealESRGAN_x4plus) ───────────────────────
    if quality in ("ultra", "pro"):
        if _is_realesrgan_ultra_cached():
            sess = _get_ultra_session()
            if sess is not None:
                try:
                    logger.info("Upscaling via RealESRGAN_x4plus Ultra model...")
                    upscaled_4x = _run_tiled_realesrgan(sess, np_rgb)
                    if scale == 4:
                        return upscaled_4x, "Super-Resolution 4× (RealESRGAN_x4plus Ultra)"
                    elif scale == 2:
                        downscaled_2x = cv2.resize(upscaled_4x, (target_w, target_h), interpolation=cv2.INTER_AREA)
                        return downscaled_2x, "Super-Resolution 2× (RealESRGAN_x4plus Ultra)"
                    elif scale == 1:
                        return cv2.resize(upscaled_4x, (target_w, target_h), interpolation=cv2.INTER_AREA), "Super-Resolution 1× (RealESRGAN_x4plus Ultra)"
                except Exception as e:
                    logger.warning(f"RealESRGAN_x4plus Ultra inference failed: {e}. Falling back to Fast tier.")
        else:
            logger.warning("RealESRGAN_x4plus Ultra weights not cached locally (~67MB). Falling back to Fast tier.")

    # ── 2. Fast Tier (realesr-general-x4v3) ─────────────────────────────
    if _is_realesrgan_fast_cached():
        sess = _get_fast_session()
        if sess is not None:
            try:
                tier_label = "realesr-general-x4v3 fallback" if quality in ("ultra", "pro") else "realesr-general-x4v3 Fast"
                logger.info(f"Upscaling via {tier_label}...")
                upscaled_4x = _run_tiled_realesrgan(sess, np_rgb)
                if scale == 4:
                    return upscaled_4x, f"Super-Resolution 4× ({tier_label})"
                elif scale == 2:
                    downscaled_2x = cv2.resize(upscaled_4x, (target_w, target_h), interpolation=cv2.INTER_AREA)
                    return downscaled_2x, f"Super-Resolution 2× ({tier_label})"
                elif scale == 1:
                    return cv2.resize(upscaled_4x, (target_w, target_h), interpolation=cv2.INTER_AREA), f"Super-Resolution 1× ({tier_label})"
            except Exception as e:
                logger.warning(f"realesr-general-x4v3 Fast inference failed: {e}. Falling back to Lanczos-4.")
    else:
        logger.warning("realesr-general-x4v3 Fast weights not cached. Falling back to Lanczos-4.")

    # ── 3. Base Fallback: Classical Lanczos-4 ────────────────────────────
    fallback_rgb = cv2.resize(np_rgb, (target_w, target_h), interpolation=cv2.INTER_LANCZOS4)
    return fallback_rgb, f"Super-Resolution {scale}× (Lanczos-4 fallback)"


def apply_enhancement(
    image_path: Path,
    params: Dict[str, Any],
    output_path: Path
) -> Tuple[List[str], int, int]:
    """
    Apply advanced enhancement pipeline to an image:
    1. Super-Resolution Upscaling (1x, 2x, 4x) via Real-ESRGAN (realesr-general-x4v3) or Pro model
    2. Non-Local Means Denoising / JPEG artifact cleanup
    3. CLAHE Local Dynamic Tone & Contrast Equalization (LAB space)
    4. Clarity / Mid-tone texture enhancement
    5. High-frequency edge deblur & sharpening
    6. Vibrance, Saturation, Contrast & Brightness balancing

    Returns:
        (applied_operations, width, height)
    """
    changes: List[str] = []

    pil_img = Image.open(image_path)
    has_alpha = pil_img.mode in ("RGBA", "LA", "PA")

    if has_alpha:
        working = pil_img.convert("RGBA")
        r, g, b, a = working.split()
        rgb_img = Image.merge("RGB", (r, g, b))
        alpha_channel = a
    else:
        rgb_img = pil_img.convert("RGB")
        alpha_channel = None

    orig_w, orig_h = rgb_img.size
    scale = int(params.get("scale", 1))
    if scale not in (1, 2, 4):
        scale = 1

    quality = str(params.get("quality", params.get("model_tier", "fast"))).lower()
    if quality in ("pro", "ultra"):
        quality = "ultra"
    else:
        quality = "fast"

    # Convert to OpenCV RGB
    np_rgb = np.array(rgb_img)

    # ── 1. Super-Resolution Upscaling ──────────────────────────────────
    if scale > 1 or quality in ("ultra", "pro"):
        target_w = orig_w * scale
        target_h = orig_h * scale

        # Upscale RGB via Real-ESRGAN / Lanczos-4
        np_rgb, method_desc = _upscale_image(np_rgb, orig_w, orig_h, scale, quality=quality)
        changes.append(f"{method_desc} ({target_w}x{target_h}px)")

        # Parallel transparency-aware alpha scaling
        if alpha_channel is not None:
            alpha_np = np.array(alpha_channel)
            alpha_np = cv2.resize(alpha_np, (target_w, target_h), interpolation=cv2.INTER_LANCZOS4)
            alpha_channel = Image.fromarray(alpha_np)

    # ── 1.5. Face & Portrait Detail Restoration (GFPGAN v1.4) ───────────
    face_restore = bool(params.get("face_restore", False))
    if face_restore:
        try:
            from image_enhancer.face_restorer import restore_faces
            face_fidelity = float(params.get("face_fidelity", 0.8))
            np_rgb, faces_count = restore_faces(np_rgb, fidelity=face_fidelity)
            if faces_count > 0:
                changes.append(f"Face Restoration (GFPGAN v1.4: {faces_count} face{'s' if faces_count > 1 else ''})")
            else:
                changes.append("Face Restoration (GFPGAN active)")
        except Exception as e:
            logger.warning(f"Face restoration step encountered exception: {e}")

    # ── 2. Denoising / Artifact Removal ────────────────────────────────
    denoise_strength = float(params.get("denoise_strength", 0.0))
    if denoise_strength > 0.5:
        h_val = int(round(denoise_strength))
        # Non-local means denoising for color images
        np_rgb = cv2.fastNlMeansDenoisingColored(
            np_rgb, None,
            h=h_val,
            hColor=h_val,
            templateWindowSize=7,
            searchWindowSize=21
        )
        changes.append(f"Denoise (strength={denoise_strength:.1f})")

    # ── 3. CLAHE (Local Adaptive Contrast) in LAB space ────────────────
    clahe_enabled = bool(params.get("clahe_enabled", True))
    if clahe_enabled:
        lab = cv2.cvtColor(np_rgb, cv2.COLOR_RGB2LAB)
        l, a_chan, b_chan = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l_clahe = clahe.apply(l)
        lab_enhanced = cv2.merge((l_clahe, a_chan, b_chan))
        np_rgb = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2RGB)
        changes.append("Adaptive Tone (CLAHE)")

    # ── 4. Clarity / Mid-tone Local Contrast ───────────────────────────
    clarity = float(params.get("clarity", 0.3))
    if clarity > 0.05:
        arr_f = np_rgb.astype(np.float32)
        blurred_mid = cv2.GaussianBlur(arr_f, (0, 0), 12.0)
        clarity_boost = arr_f + clarity * (arr_f - blurred_mid)
        np_rgb = np.clip(clarity_boost, 0, 255).astype(np.uint8)
        changes.append(f"Clarity boost (+{int(clarity * 100)}%)")

    # ── 5. Sharpening & Deblur ─────────────────────────────────────────
    sharpen_strength = float(params.get("sharpen_strength", 0.8))
    if sharpen_strength > 0.05:
        arr_f = np_rgb.astype(np.float32)
        blurred_fine = cv2.GaussianBlur(arr_f, (0, 0), 1.5)
        sharpened = arr_f + sharpen_strength * (arr_f - blurred_fine)
        np_rgb = np.clip(sharpened, 0, 255).astype(np.uint8)
        changes.append(f"Sharpen (+{int(sharpen_strength * 100)}%)")

    # Convert back to PIL Image for color adjustments
    enhanced_pil = Image.fromarray(np_rgb)

    # ── 6. Contrast ────────────────────────────────────────────────────
    contrast = float(params.get("contrast", 1.0))
    if abs(contrast - 1.0) > 0.04:
        enhancer = ImageEnhance.Contrast(enhanced_pil)
        enhanced_pil = enhancer.enhance(contrast)
        changes.append(f"Contrast ×{contrast:.2f}")

    # ── 7. Brightness ──────────────────────────────────────────────────
    brightness = float(params.get("brightness", 1.0))
    if abs(brightness - 1.0) > 0.04:
        enhancer = ImageEnhance.Brightness(enhanced_pil)
        enhanced_pil = enhancer.enhance(brightness)
        changes.append(f"Brightness ×{brightness:.2f}")

    # ── 8. Saturation / Color Vibrance ─────────────────────────────────
    saturation = float(params.get("saturation", 1.0))
    if abs(saturation - 1.0) > 0.04:
        enhancer = ImageEnhance.Color(enhanced_pil)
        enhanced_pil = enhancer.enhance(saturation)
        changes.append(f"Saturation ×{saturation:.2f}")

    # Re-attach alpha channel if present
    if alpha_channel is not None:
        result_img = Image.merge("RGBA", (*enhanced_pil.split(), alpha_channel))
    else:
        result_img = enhanced_pil

    out_w, out_h = result_img.size
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result_img.save(str(output_path), "PNG", optimize=True)

    logger.info(f"Enhanced image saved to {output_path} ({out_w}x{out_h}), changes: {changes}")
    return changes, out_w, out_h


def enhance_image(
    image_path: Path,
    output_path: Optional[Path] = None,
    scale: int = 1,
    params: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Tuple[List[str], int, int]:
    """
    Convenience wrapper for apply_enhancement.
    Supports enhance_image(image_path, output_path, scale=2, ...)
    """
    p = dict(params or {})
    p.update(kwargs)
    if scale != 1 or "scale" not in p:
        p["scale"] = scale
    if output_path is None:
        output_path = image_path.parent / f"{image_path.stem}_enhanced.png"
    return apply_enhancement(image_path=image_path, params=p, output_path=Path(output_path))


__all__ = ["apply_enhancement", "enhance_image"]

