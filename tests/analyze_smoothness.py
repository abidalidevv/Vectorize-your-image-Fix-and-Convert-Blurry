import cv2
import numpy as np
from pathlib import Path
import resvg_py

def analyze_circle_smoothness(svg_p, name):
    content = svg_p.read_text(encoding='utf-8')
    # Render at zoom=2
    png_bytes = resvg_py.svg_to_bytes(content, zoom=2)
    img = cv2.imdecode(np.frombuffer(png_bytes, np.uint8), cv2.IMREAD_GRAYSCALE)
    h, w = img.shape
    cx, cy = w / 2, h / 2
    
    # Save a 400x400 crop around the upper circular arc / crosshair intersection (like user's screenshot)
    # in original 300x300, crosshair is at (150, 150). With zoom=2 and scale=4 (if 1200x1200 viewBox) or zoom=2 on 300x300 (600x600)
    print(f"[{name}] rendered size: {w}x{h}")
    crop = img[int(cy - h*0.2):int(cy + h*0.2), int(cx - w*0.2):int(cx + w*0.2)]
    crop_p = Path(f"backend/app/temp_files/test_scratch/crop_{name}.png")
    cv2.imwrite(str(crop_p), crop)
    print(f"Saved {crop_p}")

    # Find the outer circle contour and measure its deviation from a true circle
    # Threshold dark pixels
    _, bin_dark = cv2.threshold(img, 128, 255, cv2.THRESH_BINARY_INV)
    # Mask out crosshair
    mask = np.ones_like(bin_dark)
    cross_thick = int(w * 0.02)
    mask[:, int(cx - cross_thick):int(cx + cross_thick)] = 0
    mask[int(cy - cross_thick):int(cy + cross_thick), :] = 0
    masked = cv2.bitwise_and(bin_dark, mask)
    
    cnts, _ = cv2.findContours(masked, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    print(f"[{name}] detected {len(cnts)} contours outside crosshair")
    
    # Find circle contours (round ones)
    deviations = []
    for c in cnts:
        if len(c) > 100:
            (ccx, ccy), radius = cv2.minEnclosingCircle(c)
            pts = c.reshape(-1, 2)
            dists = np.sqrt((pts[:, 0] - ccx)**2 + (pts[:, 1] - ccy)**2)
            max_dev = np.max(np.abs(dists - radius))
            mean_dev = np.mean(np.abs(dists - radius))
            deviations.append((radius, max_dev, mean_dev, len(c)))
    
    deviations.sort(key=lambda x: x[0])
    for r, mdev, meandev, pts_cnt in deviations[:5]:
        print(f"   Circle r={r:.1f}: max_dev={mdev:.2f}px, mean_dev={meandev:.2f}px ({pts_cnt} contour pts)")

# Test current binary
analyze_circle_smoothness(Path("backend/app/temp_files/test_scratch/test_bw_vectorized.svg"), "current_binary_861")
analyze_circle_smoothness(Path("backend/app/temp_files/test_scratch/out_4x_color_cutout_fs0.svg"), "nearest_color_90")
analyze_circle_smoothness(Path("backend/app/temp_files/test_scratch/test_blur_bin_4x.svg"), "smooth_blur_color_26")
analyze_circle_smoothness(Path("backend/app/temp_files/test_scratch/test_cubic_bin_4x.svg"), "smooth_cubic_color_26")
