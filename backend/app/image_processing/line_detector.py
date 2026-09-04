"""
VectorForge AI / Vectorizer AI — Fine Line & Line Art Detector / Enhancer
Detects thin lines (1-2px) in line drawings, radar/target rings, wireframes, and sketches.
Uses 2x supersampling to preserve thin contours and concentric circles without creating
trumpet-shaped flaring or corner-webbing at line junctions and intersections.
"""
import logging
from pathlib import Path
from typing import Tuple, Dict, Any

import cv2
import numpy as np

logger = logging.getLogger(__name__)


def detect_line_art(img: np.ndarray) -> Dict[str, Any]:
    """
    Detect if an image is monochrome line art and whether it contains thin delicate lines.
    """
    h, w = img.shape[:2]

    # Convert to RGB / Grayscale
    if len(img.shape) == 2:
        gray = img
        is_monochrome = True
    elif img.shape[2] == 4:
        rgb = img[:, :, :3]
        diff_rg = cv2.absdiff(rgb[:, :, 0], rgb[:, :, 1])
        diff_rb = cv2.absdiff(rgb[:, :, 0], rgb[:, :, 2])
        is_monochrome = float(np.mean(diff_rg)) < 3.0 and float(np.mean(diff_rb)) < 3.0
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    else:
        diff_rg = cv2.absdiff(img[:, :, 0], img[:, :, 1])
        diff_rb = cv2.absdiff(img[:, :, 0], img[:, :, 2])
        is_monochrome = float(np.mean(diff_rg)) < 3.0 and float(np.mean(diff_rb)) < 3.0
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    if not is_monochrome:
        return {
            "is_monochrome": False,
            "is_line_art": False,
            "has_fine_lines": False,
            "thin_line_ratio": 0.0,
        }

    # Invert binary: dark lines become 255 (foreground)
    _, bin_inv = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

    fg_pixels = int(np.count_nonzero(bin_inv))
    total_pixels = h * w
    fg_ratio = fg_pixels / max(1, total_pixels)

    # Line art check via 3x3 erosion
    kernel_cross = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
    eroded = cv2.erode(bin_inv, kernel_cross, iterations=1)
    eroded_pixels = int(np.count_nonzero(eroded))

    # Thin line ratio: proportion of foreground pixels removed by 1px erosion
    thin_line_ratio = float(1.0 - (eroded_pixels / max(1, fg_pixels)))

    is_line_art = is_monochrome and (fg_ratio < 0.45)
    has_fine_lines = is_line_art and (thin_line_ratio > 0.15)

    logger.debug(
        f"LineArt analysis: mono={is_monochrome}, fg_ratio={fg_ratio:.3f}, "
        f"thin_ratio={thin_line_ratio:.3f}, has_fine_lines={has_fine_lines}"
    )

    return {
        "is_monochrome": is_monochrome,
        "is_line_art": is_line_art,
        "has_fine_lines": has_fine_lines,
        "thin_line_ratio": round(thin_line_ratio, 4),
        "fg_ratio": round(fg_ratio, 4),
    }


def enhance_fine_lines(image_path: Path, output_path: Path, scale: int = 2) -> Tuple[Path, bool, int]:
    """
    If image contains fine line art (1-2px thin lines), supersample the image by 2x
    using bicubic interpolation. This turns 1px lines into smooth 2px anti-aliased manifolds
    without filling in junction wedges or creating flared/trumpet bulging at line intersections.
    Returns (enhanced_path, was_enhanced, scale_factor).
    """
    try:
        img = cv2.imread(str(image_path), cv2.IMREAD_UNCHANGED)
        if img is None:
            return image_path, False, 1

        analysis = detect_line_art(img)
        if not analysis["has_fine_lines"]:
            return image_path, False, 1

        logger.info(
            f"Preserving fine lines for {image_path.name} via {scale}x supersampling "
            f"(thin_line_ratio={analysis['thin_line_ratio']})"
        )

        h, w = img.shape[:2]
        # Supersample with bicubic interpolation
        upscaled = cv2.resize(img, (w * scale, h * scale), interpolation=cv2.INTER_CUBIC)

        cv2.imwrite(str(output_path), upscaled)
        return output_path, True, scale

    except Exception as e:
        logger.warning(f"Fine line supersampling failed (using original): {e}")
        return image_path, False, 1
