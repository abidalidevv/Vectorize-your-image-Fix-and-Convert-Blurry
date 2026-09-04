"""
VectorForge AI — Fine Line & Line Art Detector / Enhancer
Detects thin lines (1-2px) in line drawings, radar/target rings, wireframes, and sketches,
and enhances them so vectorizers (VTracer / Contour) do not drop them as zero-area speckles.
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

    # Convert to RGB if needed
    if len(img.shape) == 2:
        gray = img
        is_monochrome = True
    elif img.shape[2] == 4:
        # Handle alpha
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

    # Line art typically has low foreground area (< 35% of total canvas)
    # Check erosion with 3x3 cross kernel
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


def enhance_fine_lines(image_path: Path, output_path: Path) -> Tuple[Path, bool]:
    """
    If image contains fine line art, enhance thin lines slightly (sub-pixel/1px cross dilation)
    so vectorizers can trace them with 100% fidelity without treating them as 0-area noise.
    Returns (enhanced_path, was_enhanced).
    """
    try:
        img = cv2.imread(str(image_path), cv2.IMREAD_UNCHANGED)
        if img is None:
            return image_path, False

        analysis = detect_line_art(img)
        if not analysis["has_fine_lines"]:
            return image_path, False

        logger.info(
            f"Preserving fine lines for {image_path.name} "
            f"(thin_line_ratio={analysis['thin_line_ratio']})"
        )

        has_alpha = len(img.shape) == 3 and img.shape[2] == 4
        if has_alpha:
            rgb = img[:, :, :3]
            alpha = img[:, :, 3]
            gray = cv2.cvtColor(rgb, cv2.COLOR_BGR2GRAY)
            # Combine dark pixels and non-transparent pixels
            _, bin_inv = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
            bin_inv = cv2.bitwise_and(bin_inv, alpha)
        else:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
            _, bin_inv = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

        # Cross kernel dilates by 1px orthogonally to reinforce 1px strokes without rounding sharp corners
        kernel_cross = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
        dilated_inv = cv2.dilate(bin_inv, kernel_cross, iterations=1)

        # Invert back to black lines on white canvas
        dilated = cv2.bitwise_not(dilated_inv)

        if has_alpha:
            out_img = cv2.merge([dilated, dilated, dilated, alpha])
        else:
            out_img = cv2.merge([dilated, dilated, dilated])

        cv2.imwrite(str(output_path), out_img)
        return output_path, True

    except Exception as e:
        logger.warning(f"Fine line enhancement failed (using original): {e}")
        return image_path, False
