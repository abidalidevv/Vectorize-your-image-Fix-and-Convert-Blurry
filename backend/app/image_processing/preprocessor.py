"""
VectorForge AI — Image Preprocessor
OpenCV-based image enhancement pipeline.
"""
import logging
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

logger = logging.getLogger(__name__)


def apply_preprocessing(image_path: Path, params: dict, output_path: Path) -> list[str]:
    """
    Apply a chain of preprocessing operations to an image.
    Returns a list of applied operations (for user feedback).
    """
    changes = []

    # Load with Pillow (preserves alpha)
    pil_img = Image.open(image_path)
    has_alpha = pil_img.mode in ("RGBA", "LA", "PA")

    # Work in RGBA to preserve transparency
    if has_alpha:
        working = pil_img.convert("RGBA")
    else:
        working = pil_img.convert("RGB")

    # ── Background Removal ─────────────────────────────────────────────
    if params.get("bg_removal_enabled", False):
        working, applied = _remove_background(working, params)
        if applied:
            changes.append("Background removed")

    # ── Split alpha for color operations ───────────────────────────────
    if working.mode == "RGBA":
        r, g, b, a = working.split()
        rgb_img = Image.merge("RGB", (r, g, b))
    else:
        rgb_img = working
        a = None

    # ── Noise reduction ────────────────────────────────────────────────
    if params.get("denoise_enabled", False):
        strength = float(params.get("denoise_strength", 3.0))
        rgb_img = _denoise(rgb_img, strength)
        changes.append(f"Noise reduction (strength={strength:.0f})")

    # ── Anti-alias cleanup ─────────────────────────────────────────────
    if params.get("antialias_cleanup", False):
        rgb_img = _antialias_cleanup(rgb_img)
        changes.append("Anti-alias edge cleanup")

    # ── Contrast adjustment ────────────────────────────────────────────
    contrast = float(params.get("contrast", 1.0))
    if abs(contrast - 1.0) > 0.05:
        enhancer = ImageEnhance.Contrast(rgb_img)
        rgb_img = enhancer.enhance(contrast)
        changes.append(f"Contrast ×{contrast:.2f}")

    # ── Brightness adjustment ──────────────────────────────────────────
    brightness = float(params.get("brightness", 1.0))
    if abs(brightness - 1.0) > 0.05:
        enhancer = ImageEnhance.Brightness(rgb_img)
        rgb_img = enhancer.enhance(brightness)
        changes.append(f"Brightness ×{brightness:.2f}")

    # ── Saturation adjustment ──────────────────────────────────────────
    saturation = float(params.get("saturation", 1.0))
    if abs(saturation - 1.0) > 0.05:
        enhancer = ImageEnhance.Color(rgb_img)
        rgb_img = enhancer.enhance(saturation)
        changes.append(f"Saturation ×{saturation:.2f}")

    # ── Edge sharpening ────────────────────────────────────────────────
    if params.get("sharpen_enabled", False):
        strength = float(params.get("sharpen_strength", 0.5))
        rgb_img = _sharpen(rgb_img, strength)
        changes.append(f"Edge enhancement (strength={strength:.2f})")

    # ── Reassemble with alpha ──────────────────────────────────────────
    if a is not None:
        result = Image.merge("RGBA", (*rgb_img.split(), a))
    else:
        result = rgb_img

    # Save as PNG to preserve quality
    result.save(str(output_path), "PNG")
    return changes


def _denoise(img: Image.Image, strength: float) -> Image.Image:
    """Apply Non-local Means denoising via OpenCV."""
    arr = np.array(img)
    h_val = int(strength)
    denoised = cv2.fastNlMeansDenoisingColored(arr, None, h_val, h_val, 7, 21)
    return Image.fromarray(denoised)


def _sharpen(img: Image.Image, strength: float) -> Image.Image:
    """Conservative edge enhancement using unsharp mask."""
    arr = np.array(img).astype(np.float32)
    # Gaussian blur
    blurred = cv2.GaussianBlur(arr, (0, 0), 2.0)
    # Unsharp mask: original + strength * (original - blurred)
    sharpened = arr + strength * (arr - blurred)
    sharpened = np.clip(sharpened, 0, 255).astype(np.uint8)
    return Image.fromarray(sharpened)


def _antialias_cleanup(img: Image.Image) -> Image.Image:
    """
    Reduce anti-aliased edge pixels by quantizing to nearest cluster center.
    Conservative — applied at reduced strength.
    """
    arr = np.array(img).astype(np.float32)
    # Bilateral filter preserves edges while smoothing gradients
    result = cv2.bilateralFilter(arr.astype(np.uint8), 5, 50, 50)
    return Image.fromarray(result)


def _remove_background(
    img: Image.Image, params: dict
) -> Tuple[Image.Image, bool]:
    """
    Background removal via flood-fill from image border.
    Supports auto-detect (most common border color) or manual hex color.
    """
    try:
        # Convert to RGBA
        rgba = img.convert("RGBA")
        arr = np.array(rgba)
        h, w = arr.shape[:2]

        tolerance = float(params.get("bg_tolerance", 30.0))

        if params.get("bg_auto_detect", True) and not params.get("bg_color"):
            # Sample border pixels to find background color
            border_pixels = np.vstack([
                arr[0, :, :3],       # top row
                arr[-1, :, :3],      # bottom row
                arr[:, 0, :3],       # left col
                arr[:, -1, :3],      # right col
            ])
            # Use median of border pixels as background estimate
            bg_rgb = np.median(border_pixels, axis=0).astype(np.uint8)
        else:
            hex_color = params.get("bg_color", "#ffffff").lstrip("#")
            bg_rgb = np.array([
                int(hex_color[0:2], 16),
                int(hex_color[2:4], 16),
                int(hex_color[4:6], 16),
            ], dtype=np.uint8)

        # Build mask of pixels similar to background
        diff = np.abs(arr[:, :, :3].astype(int) - bg_rgb.astype(int))
        dist = np.max(diff, axis=2)
        mask = dist <= tolerance

        # Use flood fill from all four corners to restrict to connected background
        fill_mask = np.zeros((h + 2, w + 2), dtype=np.uint8)
        seed_points = [(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)]

        for (fy, fx) in seed_points:
            if mask[fy, fx]:
                cv2.floodFill(mask.astype(np.uint8), fill_mask, (fx, fy), 255,
                              loDiff=0, upDiff=0)

        connected_bg = fill_mask[1:h+1, 1:w+1] == 255

        # Apply transparency
        result = arr.copy()
        result[connected_bg, 3] = 0

        return Image.fromarray(result, "RGBA"), True

    except Exception as e:
        logger.warning(f"Background removal failed: {e}")
        return img, False
