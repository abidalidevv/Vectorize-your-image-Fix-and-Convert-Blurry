import resvg_py
from pathlib import Path

for name in [
    'opt_1_color_cutout_fs1',
    'opt_1_color_stacked_fs1',
    'opt_2_color_cutout_fs1',
    'opt_2_color_stacked_fs1',
]:
    svg_path = Path(f'backend/app/temp_files/bce3bab1-b124-4d30-a88f-88a453609844/{name}.svg')
    svg = svg_path.read_text(encoding='utf-8')
    png = resvg_py.svg_to_bytes(svg, zoom=3.0)
    out_png = Path(f'backend/app/temp_files/bce3bab1-b124-4d30-a88f-88a453609844/{name}.png')
    out_png.write_bytes(png)
    print(f'Rendered {name}.png')
