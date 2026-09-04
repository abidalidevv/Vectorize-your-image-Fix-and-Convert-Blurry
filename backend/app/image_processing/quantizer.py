"""
VectorForge AI — Color Quantizer
High-quality palette reduction using k-means + median cut.
"""
import logging
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


def quantize_image(
    image_path: Path,
    output_path: Path,
    num_colors: int = 8,
    method: str = "auto",
) -> dict:
    """
    Quantize image colors to a fixed palette.
    Returns palette info and saves quantized image to output_path.
    """
    pil_img = Image.open(image_path)
    has_alpha = pil_img.mode in ("RGBA", "LA", "PA")

    if has_alpha:
        rgba = pil_img.convert("RGBA")
        rgb_img = pil_img.convert("RGB")
        alpha_channel = np.array(rgba)[:, :, 3]
    else:
        rgb_img = pil_img.convert("RGB")
        alpha_channel = None

    img_np = np.array(rgb_img)

    # Choose method
    if method == "auto":
        # Use kmeans for ≤ 32 colors (better quality), median cut for more
        method = "kmeans" if num_colors <= 32 else "median_cut"

    if method == "kmeans":
        quantized_np, palette, labels = _kmeans_quantize(img_np, num_colors)
    else:
        quantized_np, palette, labels = _median_cut_quantize(img_np, num_colors)

    # Build palette info
    h, w = img_np.shape[:2]
    total_pixels = h * w
    palette_info = []

    for i, color in enumerate(palette):
        r, g, b = int(color[0]), int(color[1]), int(color[2])
        count = int(np.sum(labels == i))
        percentage = round(count / total_pixels * 100, 2) if total_pixels > 0 else 0.0
        palette_info.append({
            "index": i,
            "hex": f"#{r:02x}{g:02x}{b:02x}",
            "rgb": [r, g, b],
            "percentage": percentage,
            "enabled": True,
            "is_background": False,
        })

    # Sort by percentage descending
    palette_info.sort(key=lambda x: x["percentage"], reverse=True)
    for i, p in enumerate(palette_info):
        p["index"] = i

    # Save quantized image
    result_img = Image.fromarray(quantized_np.astype(np.uint8))
    if alpha_channel is not None:
        result_rgba = result_img.convert("RGBA")
        arr = np.array(result_rgba)
        arr[:, :, 3] = alpha_channel
        result_img = Image.fromarray(arr, "RGBA")

    result_img.save(str(output_path), "PNG")

    return {
        "num_colors": num_colors,
        "actual_colors": len(palette),
        "palette": palette_info,
        "method_used": method,
    }


def _kmeans_quantize(img: np.ndarray, k: int) -> tuple:
    """K-means color quantization using OpenCV."""
    h, w = img.shape[:2]
    flat = img.reshape(-1, 3).astype(np.float32)

    # If image is huge, subsample for kmeans training
    if len(flat) > 50000:
        sample_idx = np.random.choice(len(flat), 50000, replace=False)
        sample = flat[sample_idx]
    else:
        sample = flat

    k = min(k, len(np.unique(sample.view(np.dtype((np.void, sample.dtype.itemsize * sample.shape[1]))).ravel())))
    k = max(1, k)

    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 50, 0.1)
    _, sample_labels, centers = cv2.kmeans(
        sample, k, None, criteria, 10, cv2.KMEANS_PP_CENTERS
    )

    # Assign all pixels to nearest center
    flat_f = flat
    diffs = flat_f[:, None, :] - centers[None, :, :]  # (N, K, 3)
    dists = np.sum(diffs ** 2, axis=2)  # (N, K)
    labels = np.argmin(dists, axis=1).reshape(h, w)

    quantized = centers[labels].astype(np.uint8)
    return quantized, centers.astype(np.uint8), labels


def _median_cut_quantize(img: np.ndarray, k: int) -> tuple:
    """
    Median cut quantization via Pillow's built-in quantizer.
    Returns (quantized_rgb_array, palette, labels).
    """
    pil = Image.fromarray(img.astype(np.uint8))
    quantized_pil = pil.quantize(colors=k, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)

    palette_raw = quantized_pil.getpalette()
    num_colors = k
    palette = []
    for i in range(num_colors):
        palette.append([palette_raw[i*3], palette_raw[i*3+1], palette_raw[i*3+2]])
    palette = np.array(palette, dtype=np.uint8)

    label_array = np.array(quantized_pil)

    # Reconstruct RGB
    quantized_rgb = palette[label_array]

    return quantized_rgb, palette, label_array
