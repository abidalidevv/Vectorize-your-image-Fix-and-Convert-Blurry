"""
VectorForge AI — Image Analyzer
Analyzes image characteristics to recommend vectorization mode.
"""
import logging
from pathlib import Path
from typing import Tuple

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


def analyze_image(image_path: Path) -> dict:
    """
    Full image analysis returning characteristics and mode recommendation.
    """
    try:
        pil_img = Image.open(image_path)
        pil_rgb = pil_img.convert("RGBA") if pil_img.mode == "RGBA" else pil_img.convert("RGB")
        has_alpha = pil_img.mode in ("RGBA", "LA", "PA")

        img_np = np.array(pil_img.convert("RGB"))
        h, w = img_np.shape[:2]

        # ── Color analysis ─────────────────────────────────────────────────
        small = _resize_for_analysis(img_np, max_dim=256)

        # Estimate unique colors
        flat = small.reshape(-1, 3)
        # Quantize to 5-bit for estimation
        quantized = (flat >> 3).astype(np.uint32)
        unique_count = len(np.unique(quantized[:, 0] * 1024 + quantized[:, 1] * 32 + quantized[:, 2]))

        # Saturation
        hsv = cv2.cvtColor(small, cv2.COLOR_RGB2HSV)
        saturation_mean = float(np.mean(hsv[:, :, 1])) / 255.0
        saturation_std = float(np.std(hsv[:, :, 1])) / 255.0

        # Grayscale check
        r, g, b = img_np[:, :, 0], img_np[:, :, 1], img_np[:, :, 2]
        channel_diff = float(np.mean(np.abs(r.astype(int) - g.astype(int)) +
                                     np.abs(g.astype(int) - b.astype(int)) +
                                     np.abs(r.astype(int) - b.astype(int))))
        is_grayscale = channel_diff < 15.0

        # ── Edge density ───────────────────────────────────────────────────
        gray = cv2.cvtColor(small, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        edge_density = float(np.mean(edges > 0))

        # ── Local variance (complexity) ────────────────────────────────────
        kernel = np.ones((4, 4), np.float32) / 16
        mean_sq = cv2.filter2D(gray.astype(np.float32) ** 2, -1, kernel)
        mean_val = cv2.filter2D(gray.astype(np.float32), -1, kernel)
        local_var = mean_sq - mean_val ** 2
        complexity_score = float(np.mean(local_var)) / (255.0 ** 2)

        # ── Dominant colors ────────────────────────────────────────────────
        dominant_colors = _extract_dominant_colors(small, n=8)

        # ── Line art detection ─────────────────────────────────────────────
        from image_processing.line_detector import detect_line_art
        line_info = detect_line_art(img_np)

        # ── Mode recommendation ────────────────────────────────────────────
        recommended_mode, confidence, notes = _recommend_mode(
            unique_count, saturation_mean, saturation_std,
            is_grayscale, edge_density, complexity_score
        )

        # If thin line art was detected, ensure recommendation is bw
        if line_info["has_fine_lines"] and is_grayscale:
            recommended_mode = "bw"
            confidence = max(confidence, 0.95)
            notes = "Fine line art / drawing detected with thin contours. Line preservation recommended."

        return {
            "recommended_mode": recommended_mode,
            "confidence": confidence,
            "color_count_estimate": int(unique_count),
            "dominant_colors": dominant_colors,
            "is_grayscale": is_grayscale,
            "has_transparency": has_alpha,
            "edge_density": round(edge_density, 4),
            "complexity_score": round(complexity_score, 6),
            "saturation_mean": round(saturation_mean, 4),
            "is_line_art": line_info["is_line_art"],
            "has_fine_lines": line_info["has_fine_lines"],
            "thin_line_ratio": line_info["thin_line_ratio"],
            "width": w,
            "height": h,
            "notes": notes,
        }

    except Exception as e:
        logger.error(f"Image analysis failed: {e}", exc_info=True)
        raise


def _resize_for_analysis(img: np.ndarray, max_dim: int = 256) -> np.ndarray:
    h, w = img.shape[:2]
    if max(h, w) <= max_dim:
        return img
    scale = max_dim / max(h, w)
    new_w, new_h = max(1, int(w * scale)), max(1, int(h * scale))
    return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)


def _extract_dominant_colors(img: np.ndarray, n: int = 8) -> list[dict]:
    """K-means dominant color extraction on small image."""
    flat = img.reshape(-1, 3).astype(np.float32)
    # Downsample for speed
    if len(flat) > 2000:
        idx = np.random.choice(len(flat), 2000, replace=False)
        flat = flat[idx]

    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.2)
    n = min(n, len(flat))
    try:
        _, labels, centers = cv2.kmeans(flat, n, None, criteria, 5, cv2.KMEANS_RANDOM_CENTERS)
        counts = np.bincount(labels.flatten(), minlength=n)
        total = counts.sum()
        colors = []
        for i, center in enumerate(centers):
            r, g, b = int(center[0]), int(center[1]), int(center[2])
            colors.append({
                "hex": f"#{r:02x}{g:02x}{b:02x}",
                "rgb": [r, g, b],
                "percentage": float(round(float(counts[i]) / float(total) * 100, 1)),
                "index": i,
            })
        colors.sort(key=lambda x: x["percentage"], reverse=True)
        return colors
    except Exception as e:
        logger.warning(f"Dominant color extraction failed: {e}")
        return []


def _recommend_mode(
    unique_colors: int,
    sat_mean: float,
    sat_std: float,
    is_grayscale: bool,
    edge_density: float,
    complexity: float,
) -> Tuple[str, float, str]:
    """
    Rule-based mode recommendation.
    Returns (mode, confidence, notes).
    """
    notes_parts = []

    # Black & white drawing
    if is_grayscale and unique_colors < 50:
        notes_parts.append("Grayscale, few unique tones detected.")
        if edge_density > 0.05:
            return "bw", 0.90, "Monochrome/sketch with clear edges. " + " ".join(notes_parts)
        return "sketch", 0.80, "Low-saturation sketch/grayscale. " + " ".join(notes_parts)

    # Logo / clipart (flat colors, low complexity)
    if unique_colors < 200 and sat_mean > 0.15 and complexity < 0.008:
        notes_parts.append(f"~{unique_colors} unique color zones, low complexity.")
        return "logo", 0.85, "Flat-color logo/clipart detected. " + " ".join(notes_parts)

    # Sketch (high edges, low saturation)
    if sat_mean < 0.10 and edge_density > 0.08:
        return "sketch", 0.75, "High edge density, low saturation — sketch mode."

    # Photo (high complexity, many colors)
    if unique_colors > 500 or complexity > 0.015:
        notes_parts.append(f"High complexity ({complexity:.4f}), ~{unique_colors} colors.")
        return "photo", 0.80, "Photographic content detected. " + " ".join(notes_parts)

    # Default: logo for moderate complexity
    return "logo", 0.60, "Moderate complexity — defaulting to logo mode. Manual override recommended."
