import vtracer
from pathlib import Path
import re

out = 'backend/test_check.svg'

for ld in [4, 8, 12, 16, 20]:
    for fs in [0, 1, 2]:
        for cp in [6, 7, 8]:
            vtracer.convert_image_to_svg_py(
                'samples/test_logo.png', out,
                'color',
                'stacked',
                'spline',
                fs,
                cp,
                ld,
                60,
                2.5,
                10,
                45,
                5
            )
            svg = Path(out).read_text()
            Path(out).unlink(missing_ok=True)
            
            fills = re.findall(r'fill="([^"]+)"', svg)
            yellow_paths = [m.group(0) for m in re.finditer(r'<path[^>]+fill="#F[0-9A-Fa-f]{5}"[^>]*>', svg)]
            has_extra_yellow = any('400' in p and '0 199' in p for p in yellow_paths)
            brown_paths = [p for p in fills if p.startswith('#9') or p.startswith('#A') or p.startswith('#8')]
            
            print(f"ld={ld:2d} fs={fs} cp={cp}: extra_yellow={str(has_extra_yellow):5s}, brown_count={len(brown_paths):2d}, total_paths={len(fills):2d}")
