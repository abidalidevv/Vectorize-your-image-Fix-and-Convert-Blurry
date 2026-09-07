import cv2, numpy as np, resvg_py
from pathlib import Path

# Render test_sdf_clean.svg at 2000% zoom (scale = 20 on 300x300, which is zoom=5 on 1200x1200)
svg_clean = Path('backend/app/temp_files/test_scratch/test_sdf_clean.svg').read_text()
png_bytes = resvg_py.svg_to_bytes(svg_clean, zoom=5)
img = cv2.imdecode(np.frombuffer(png_bytes, np.uint8), cv2.IMREAD_GRAYSCALE)
h, w = img.shape
print('Rendered 2000% size:', w, 'x', h)

# Crop around the innermost circle and horizontal axis junction (around x=750, y=3000 in 6000x6000)
# Original 300x300: (150, 150) is center.
# The user zoomed in on the left arc near the horizontal crosshair:
# x in 300x300 is around 120-150, y is around 150.
# In 6000x6000: x=2400..3000, y=2800..3200
crop = img[2700:3300, 2400:3000]
cv2.imwrite('backend/app/temp_files/test_scratch/crop_2000_sdf_clean.png', crop)
print('Saved crop_2000_sdf_clean.png')
