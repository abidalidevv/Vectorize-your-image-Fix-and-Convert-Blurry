# Pro Models Directory

This folder is dedicated to Pro Tier AI Models:
1. **Pro Image Enhancer Model** (Super-resolution, deblur, fine texture)
2. **Pro Background Matting Model** (Hair and boundary precision segmentation)

Place model weights in `backend/app/models_pro/weights/`.
The Pro modules in `enhancer_pro.py` and `bg_remover_pro.py` will automatically load them.
