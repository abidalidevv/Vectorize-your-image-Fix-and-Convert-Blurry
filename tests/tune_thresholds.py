import vtracer
import cv2
import numpy as np
from pathlib import Path
import re
import resvg_py

img_p = Path('backend/app/temp_files/test_scratch/cand_v6_s4_sdf_cutout.png')

for ct in [30, 45, 60, 75, 90, 120, 150]:
    for lt in [2.0, 4.0, 8.0, 12.0, 16.0]:
        out_svg = Path(f'backend/app/temp_files/test_scratch/tune_ct{ct}_lt{int(lt)}.svg')
        vtracer.convert_image_to_svg_py(
            str(img_p),
            str(out_svg),
            'color',
            'cutout',
            'spline',
            0,
            2,
            16,
            ct,
            lt,
            10,
            45,
            6
        )
        content = out_svg.read_text(encoding='utf-8')
        # fix viewBox
        def fix_root(m):
            tag = m.group(0)
            tag = re.sub(r'\s+width="[^"]*"', '', tag)
            tag = re.sub(r'\s+height="[^"]*"', '', tag)
            tag = re.sub(r'\s+viewBox="[^"]*"', '', tag)
            return f'{tag[:-1]} width="300" height="300" viewBox="0 0 1200 1200">'
        content = re.sub(r'<svg\b[^>]*>', fix_root, content, count=1)
        out_svg.write_text(content, encoding='utf-8')

        paths = re.findall(r'<path[^>]*>', content)
        # Measure smoothness of circle in rendered output
        png_bytes = resvg_py.svg_to_bytes(content, zoom=2)
        r_img = cv2.imdecode(np.frombuffer(png_bytes, np.uint8), cv2.IMREAD_GRAYSCALE)
        
        # Count total commands in path 1 (outer circular ring)
        p1 = paths[1] if len(paths) > 1 else paths[0]
        c_count = p1.count('C')
        l_count = p1.count('L')
        print(f"ct={ct:3d}, lt={lt:4.1f}: paths={len(paths):2d}, p1_C={c_count:3d}, p1_L={l_count:3d}")
