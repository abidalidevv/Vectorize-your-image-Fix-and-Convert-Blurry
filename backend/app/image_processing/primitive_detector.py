import cv2
import numpy as np
from pathlib import Path


def detect_primitives(image_path: Path) -> dict:
    """
    Detect circles and straight lines in a B&W line-art image using Hough transforms.
    Returns detected shapes plus what fraction of the foreground they explain.
    """
    img = cv2.imread(str(image_path), cv2.IMREAD_UNCHANGED)
    if img is None:
        return {"circles": [], "lines": [], "stroke_width": 2.0, "coverage": 0.0}

    if len(img.shape) == 3 and img.shape[2] == 4:
        rgb = img[:, :, :3]
        alpha = img[:, :, 3] / 255.0
        white = np.ones_like(rgb) * 255
        comp = (rgb * alpha[:, :, None] + white * (1.0 - alpha[:, :, None])).astype(np.uint8)
        gray = cv2.cvtColor(comp, cv2.COLOR_BGR2GRAY)
    else:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img

    h, w = gray.shape[:2]
    _, fg_mask = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
    foreground_count = int(np.count_nonzero(fg_mask))
    if foreground_count == 0:
        return {"circles": [], "lines": [], "stroke_width": 2.0, "coverage": 0.0}

    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    circles = []
    # Try HOUGH_GRADIENT_ALT first (handles concentric circles with high accuracy)
    try:
        circles_alt = cv2.HoughCircles(
            blurred, cv2.HOUGH_GRADIENT_ALT, dp=1.5, minDist=int(min(h, w) * 0.05),
            param1=300, param2=0.6, minRadius=int(min(h, w) * 0.02), maxRadius=int(min(h, w) * 0.6)
        )
        if circles_alt is not None:
            raw_c = circles_alt[0] if circles_alt.ndim == 3 else circles_alt
            for c in raw_c:
                circles.append((float(c[0]), float(c[1]), float(c[2])))
    except Exception:
        pass

    if not circles:
        circles_raw = cv2.HoughCircles(
            blurred, cv2.HOUGH_GRADIENT, dp=1, minDist=max(h, w) * 0.03,
            param1=80, param2=25, minRadius=int(min(h, w) * 0.02), maxRadius=int(min(h, w) * 0.6)
        )
        if circles_raw is not None:
            raw_c = circles_raw[0] if circles_raw.ndim == 3 else circles_raw
            for c in raw_c:
                circles.append((float(c[0]), float(c[1]), float(c[2])))

    edges = cv2.Canny(gray, 50, 150)
    lines_raw = cv2.HoughLinesP(
        edges, 1, np.pi / 180, threshold=60,
        minLineLength=int(min(h, w) * 0.3), maxLineGap=10
    )
    raw_lines = []
    if lines_raw is not None:
        lines_iter = lines_raw[:, 0] if lines_raw.ndim == 3 else lines_raw
        for l in lines_iter:
            raw_lines.append(tuple(float(v) for v in l))

    lines = []
    for (x1, y1, x2, y2) in raw_lines:
        angle = np.arctan2(y2 - y1, x2 - x1)
        if abs(np.sin(angle)) < 0.05:
            y_avg = (y1 + y2) / 2
            lines.append((0.0, y_avg, float(w), y_avg))
        elif abs(np.cos(angle)) < 0.05:
            x_avg = (x1 + x2) / 2
            lines.append((x_avg, 0.0, x_avg, float(h)))

    dist = cv2.distanceTransform(fg_mask, cv2.DIST_L2, 5)
    avg_half_width = float(np.sum(dist) / foreground_count) if foreground_count else 1.0
    stroke_width = max(1.0, avg_half_width * 1.6)

    h_lines = [ln for ln in lines if ln[1] == ln[3]]
    v_lines = [ln for ln in lines if ln[0] == ln[2]]

    merge_tol = max(6.0, stroke_width * 1.5)

    def _dedup(group, key_idx):
        unique = []
        for ln in group:
            if not any(abs(ln[key_idx] - o[key_idx]) < merge_tol for o in unique):
                unique.append(ln)
        return unique

    lines = _dedup(h_lines, 1) + _dedup(v_lines, 0)

    primitive_mask = np.zeros_like(fg_mask)
    for (cx, cy, r) in circles:
        cv2.circle(primitive_mask, (int(round(cx)), int(round(cy))), int(round(r)), 255, max(1, int(round(stroke_width))))
    for (x1, y1, x2, y2) in lines:
        cv2.line(primitive_mask, (int(round(x1)), int(round(y1))), (int(round(x2)), int(round(y2))), 255, max(1, int(round(stroke_width))))

    dilated = cv2.dilate(primitive_mask, np.ones((5, 5), np.uint8))
    explained = cv2.bitwise_and(fg_mask, dilated)
    coverage = float(np.count_nonzero(explained)) / float(foreground_count)

    return {"circles": circles, "lines": lines, "stroke_width": stroke_width, "coverage": coverage}


def build_primitive_svg(primitives: dict, width: int, height: int, has_alpha: bool) -> str:
    sw = primitives["stroke_width"]
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg version="1.1" xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
    ]
    if not has_alpha:
        parts.append('<rect width="100%" height="100%" fill="#ffffff"/>')
    for (cx, cy, r) in primitives["circles"]:
        parts.append(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" fill="none" stroke="#000000" stroke-width="{sw:.2f}"/>')
    for (x1, y1, x2, y2) in primitives["lines"]:
        parts.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="#000000" stroke-width="{sw:.2f}"/>')
    parts.append('</svg>')
    return "\n".join(parts)
