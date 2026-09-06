"""
Pre-download GFPGAN v1.4, YuNet Face Detector, and LaMa Inpainting models for VectorForge AI.
"""
import os
import sys
import time
import urllib.request
from pathlib import Path

MODELS = [
    {
        "name": "YuNet Face Detector (OpenCV Zoo)",
        "url": "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx",
        "dest": Path.home() / ".cache" / "gfpgan" / "face_detection_yunet.onnx",
        "min_size": 100_000,
    },
    {
        "name": "GFPGAN v1.4 (Face Restoration)",
        "url": "https://huggingface.co/datasets/Gourieff/ReActor/resolve/main/models/facerestore_models/GFPGANv1.4.onnx",
        "dest": Path.home() / ".cache" / "gfpgan" / "GFPGANv1.4.onnx",
        "min_size": 300_000_000,
    },
    {
        "name": "LaMa FP32 (Magic Eraser Inpainting)",
        "url": "https://huggingface.co/Carve/LaMa-ONNX/resolve/main/lama_fp32.onnx",
        "dest": Path.home() / ".cache" / "lama" / "lama_fp32.onnx",
        "min_size": 150_000_000,
    },
]

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

for m in MODELS:
    dest = m["dest"]
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size >= m["min_size"]:
        print(f"[OK] {m['name']} already cached ({round(dest.stat().st_size / (1024*1024), 1)} MB): {dest}")
        continue

    print(f"[DOWNLOADING] {m['name']} from {m['url']}...")
    t0 = time.time()
    try:
        urllib.request.urlretrieve(m["url"], str(dest))
        sz_mb = round(dest.stat().st_size / (1024 * 1024), 1)
        print(f"[SUCCESS] Downloaded {m['name']} in {round(time.time() - t0, 1)}s ({sz_mb} MB) -> {dest}")
    except Exception as e:
        print(f"[ERROR] Failed to download {m['name']}: {e}")
