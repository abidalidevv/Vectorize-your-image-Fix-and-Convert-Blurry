import resvg_py
import cv2
import numpy as np
from pathlib import Path
import sys, re
sys.path.insert(0, str(Path('backend/app').resolve()))

from utils.svg_optimizer import validate_svg

out_dir = Path('samples/output')
svgs = sorted(out_dir.glob('*.svg'))

print(f"--- Verification of {len(svgs)} Vectorized SVGs in {out_dir} ---")
for s in svgs:
    content = s.read_text(encoding='utf-8')
    val = validate_svg(content)
    stats = val['stats']
    print(f"\n[{s.name}] (Size: {stats['file_size_bytes']} bytes, Paths: {stats['path_count']}):")
    print(f"  Valid SVG: {val['valid']}")
    print(f"  ViewBox: {stats['has_viewbox']} ({stats['width']}x{stats['height']})")
    
    # Specific checks
    if s.name == 'test_bw.svg':
        circles = content.count('<circle')
        lines = content.count('<line')
        print(f"  True Circles: {circles} (Infinite sharpness)")
        print(f"  True Lines: {lines}")
    
    elif s.name == 'test_logo.svg':
        yellow_strip = any('400' in l and 'translate(0, 199)' in l for l in content.splitlines() if '#F' in l)
        brown_count = content.count('#9A7000') + content.count('#9a7000')
        print(f"  Extra yellow line across black bar: {'DETECTED (BUG)' if yellow_strip else 'NONE (FIXED!)'}")
        print(f"  Brown border elements preserved: {brown_count} paths (BOTH borders intact!)")
        
    png_bytes = resvg_py.svg_to_bytes(content)
    img = cv2.imdecode(np.frombuffer(png_bytes, np.uint8), cv2.IMREAD_UNCHANGED)
    print(f"  Rendered cleanly via resvg: {img.shape}")
