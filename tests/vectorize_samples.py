import cv2
import numpy as np
import resvg_py
import sys, re, vtracer
from pathlib import Path
sys.path.insert(0, str(Path('backend/app').resolve()))

from vectorization.vtracer_engine import VTracerEngine
from vectorization.engine_selector import select_and_trace
from utils.svg_optimizer import optimize_svg, validate_svg, ensure_viewbox

samples_dir = Path('samples')
output_dir = samples_dir / 'output'
output_dir.mkdir(exist_ok=True)

engine = VTracerEngine()

# 1. test_bw.png
# Best method: Primitive Detection (trace_bw)
src_bw = samples_dir / 'test_bw.png'
out_bw = output_dir / 'test_bw.svg'
res_bw = engine.trace_bw(src_bw, out_bw, {'use_primitive_detection': True})
print('test_bw:', res_bw.get('engine'), 'size:', out_bw.stat().st_size)

# 2. test_logo.png
# Best method: Cutout mode with filter_speckle=0 and background rect to prevent yellow bleed and preserve brown border
src_logo = samples_dir / 'test_logo.png'
out_logo = output_dir / 'test_logo.svg'
vtracer.convert_image_to_svg_py(
    str(src_logo), str(out_logo),
    'color', 'cutout', 'spline', 0, 8, 12, 60, 2.0, 15, 45, 6
)
# Add base background rect and ensure viewbox
svg_logo = out_logo.read_text(encoding='utf-8')
svg_logo = ensure_viewbox(svg_logo)
# If no full-bleed rect exists, insert background fill #F0F4FF
if '<rect width="100%" height="100%"' not in svg_logo:
    svg_logo = re.sub(r'(<svg\b[^>]*>)', r'\1\n<rect width="100%" height="100%" fill="#F0F4FF"/>', svg_logo, count=1)
out_logo.write_text(svg_logo, encoding='utf-8')
print('test_logo: Cutout/No-Bleed, size:', out_logo.stat().st_size)

# 3. test_complex.png
# Best method: Stacked mode high preset (smooth circles, 0 seam holes)
src_complex = samples_dir / 'test_complex.png'
out_complex = output_dir / 'test_complex.svg'
res_complex = select_and_trace(src_complex, out_complex, {'image_mode': 'auto', 'quality_preset': 'high'})
svg_comp = ensure_viewbox(out_complex.read_text(encoding='utf-8'))
out_complex.write_text(svg_comp, encoding='utf-8')
print('test_complex:', res_complex.get('engine'), 'size:', out_complex.stat().st_size)

# 4. test_multicolor.png
# Best method: High quality spline tracing
src_multi = samples_dir / 'test_multicolor.png'
out_multi = output_dir / 'test_multicolor.svg'
res_multi = select_and_trace(src_multi, out_multi, {'image_mode': 'auto', 'quality_preset': 'high', 'filter_speckle': 0})
svg_multi = ensure_viewbox(out_multi.read_text(encoding='utf-8'))
out_multi.write_text(svg_multi, encoding='utf-8')
print('test_multicolor:', res_multi.get('engine'), 'size:', out_multi.stat().st_size)

# 5. test_transparent.png
# Best method: Stacked with alpha preservation
src_trans = samples_dir / 'test_transparent.png'
out_trans = output_dir / 'test_transparent.svg'
res_trans = select_and_trace(src_trans, out_trans, {'image_mode': 'auto', 'quality_preset': 'high'})
svg_trans = ensure_viewbox(out_trans.read_text(encoding='utf-8'))
out_trans.write_text(svg_trans, encoding='utf-8')
print('test_transparent:', res_trans.get('engine'), 'size:', out_trans.stat().st_size)

# Also copy to root samples/output if root samples exists
root_samples = Path('..') / 'samples'
if root_samples.exists():
    root_out = root_samples / 'output'
    root_out.mkdir(exist_ok=True)
    import shutil
    for f in output_dir.glob('*.svg'):
        shutil.copy2(f, root_out / f.name)
    print('Copied to root samples/output')
