import sys
sys.path.insert(0, 'backend/app')
import cv2, resvg_py, numpy as np, re
from pathlib import Path
from vectorization.vtracer_engine import VTracerEngine
from utils.svg_optimizer import validate_svg

src = Path('samples/test_bw.png')
out_svg = Path('backend/app/temp_files/test_scratch/verified_trace_bw.svg')

engine = VTracerEngine()
res = engine.trace_bw(src, out_svg, {})
print('trace_bw success:', res['success'])

svg = out_svg.read_text(encoding='utf-8')
stats = validate_svg(svg)['stats']
print('Path count:', stats.get('path_count'))
print('File size:', len(svg))

# Check for Bézier curves
bezier_count = len(re.findall(r'[Cc]', svg))
print('Bézier curve command count:', bezier_count)

# Render at 5x (1500x1500) and take a crop at 2000%
png_bytes = resvg_py.svg_to_bytes(svg, zoom=5)
r_img = cv2.imdecode(np.frombuffer(png_bytes, np.uint8), cv2.IMREAD_GRAYSCALE)
crop = r_img[650:850, 550:750]
crop_path = Path('backend/app/temp_files/test_scratch/crop_2000_verified.png')
cv2.imwrite(str(crop_path), crop)
print('Saved verified crop:', crop_path)
