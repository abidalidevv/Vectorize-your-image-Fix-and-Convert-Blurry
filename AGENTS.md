# 🤖 VectorForge AI — Antigravity & AI Agent Instructions (AGENTS.md)

> **Master Guide for Antigravity & Future AI Pair Programmers**  
> **Author**: [Abid Ali](https://abidalidev.com) • [GitHub (@abidalidevv)](https://github.com/abidalidevv)  
> **Repository**: [Vectorize-your-image-Fix-and-Convert-Blurry](https://github.com/abidalidevv/Vectorize-your-image-Fix-and-Convert-Blurry)  
> **Status**: Production-Ready • 23/23 Unit Tests Passing 100% Locally

---

## 1. Project Overview & Philosophy

**VectorForge AI** is a Windows-native, local-first, free and open-source raster-to-vector studio. It converts raster images (PNG, JPG, BMP, WebP) into pure, scalable Bézier curve SVG vector paths and provides three neural studios (Magic Eraser, Background Remover, Image Enhancer) without relying on any cloud API, external telemetry, or subscription fees.

- **Backend**: Python 3.10+ (FastAPI + OpenCV + Rust VTracer + ONNX Runtime + resvg-py).
- **Frontend**: React 19 + TypeScript + Vite + Zustand + Vanilla CSS (Glassmorphic dark design).
- **Core Vectorizer**: Rust VTracer wrapped in Python (`vtracer_engine.py`) with specialized geometric pre/post-processors.

---

## 2. The 7 Golden Rules of VectorForge AI Vectorization

Any AI assistant modifying `backend/app/vectorization/` or image processing pipelines **MUST obey these 7 architectural rules**:

### 1. Cutout Hierarchy Mode is Mandatory (`hierarchical = "cutout"`)
- **Do NOT switch to `stacked` mode for color vectorization**.
- In `stacked` mode, VTracer traces shapes as solid polygons stacked on top of one another. Curve-fitting mismatches cause underlying dark shapes (e.g. dark brown wedges under triangles) to protrude into transparent space and leak outside borders.
- In `cutout` mode, all shapes are non-overlapping planar paths (adjacent puzzle pieces). Outlines and borders are traced cleanly without underlying ghost polygons.

### 2. Canvas Background Rect Injection for Opaque Images
- In `cutout` mode, adjacent vector paths can show sub-pixel antialiasing seams (alpha < 255) when rendered against a transparent canvas.
- To eliminate seams completely, `vtracer_engine.py` automatically injects:
  ```xml
  <rect width="100%" height="100%" fill="{bg_color}"/>
  ```
  as the very first element for opaque images (matching the dominant canvas color). Never remove this logic!

### 3. Connected-Component Anti-Alias Filtering (`MAX_ANTIALIAS_COMPONENT_PX = 40`)
- Simple percentage-based color merging (`pct < 0.7%`) fails on thin strokes because their total pixel count is low, causing legitimate outlines (like dark brown borders) to be accidentally merged into nearby fills.
- In `vtracer_engine.py`, `cv2.connectedComponentsWithStats` is used to check `max_component_size`. Isolated anti-alias blend noise (tiny disconnected clusters < 40px at corner intersections) is safely merged, while long continuous thin outlines are preserved.

### 4. Primitive Detector Axis-Specific Line Deduplication
- In `backend/app/image_processing/primitive_detector.py`, horizontal lines must be deduplicated across Y coordinates (`[1]` and `[3]`), and vertical lines across X coordinates (`[0]` and `[2]`). Checking the wrong axis previously split horizontal lines in circles into two pieces.

### 5. Always Use Positional Arguments for VTracer
- `vtracer.convert_image_to_svg_py` takes **positional arguments only**. Calling it with keyword arguments (`input_path=...`) will throw a Python TypeError.

### 6. Always Inject `viewBox` in Generated SVGs
- Every SVG produced must pass through `utils.svg_optimizer.ensure_viewbox(svg_content)` to guarantee responsive scaling and prevent clipping in browsers and vector editors.

### 7. High-Resolution Rasterization via `resvg_py`
- For PNG export, always use `resvg_py` (Rust-based resvg engine) at 1x, 2x, 4x, or 8x scale to produce crisp raster renders from SVG paths.

---

## 3. Neural Studios & Model Weight Management

All heavy neural network weights (`.onnx`, `.pth`) are strictly stored under `backend/app/weights/` and are **gitignored**:

| Model | Purpose | Default / Path | Size |
|---|---|---|---|
| **YuNet** | Face Detection | `backend/app/weights/face_detection_yunet_2023mar.onnx` | ~336 KB |
| **GFPGAN v1.4** | Face Restoration | `backend/app/weights/GFPGANv1.4.onnx` | ~348 MB |
| **LaMa FP32** | Magic Eraser (Inpainting) | `backend/app/weights/lama_fp32.onnx` | ~208 MB |
| **Real-ESRGAN x4v3** | Image Enhancer (Fast) | `backend/app/weights/realesr-general-x4v3.onnx` | ~4.9 MB |
| **Real-ESRGAN x4plus** | Image Enhancer (Ultra) | `backend/app/weights/RealESRGAN_x4plus.onnx` | ~67.1 MB |
| **BiRefNet** | Background Remover (Ultra) | `backend/app/weights/birefnet-general.onnx` | ~972 MB |
| **IS-Net** | Background Remover (Fast) | `backend/app/weights/isnet-general-use.onnx` | ~176 MB |

### 1-Click Model Downloader
Users and developers can download all models offline with a single click:
- **Windows**: Run `download_models.bat` (launches `scripts/download_pro_models.py` with automatic retry).
- **Linux / macOS**: Run `./download_models.sh`.

---

## 4. How to Run & Verify

### Start Backend (FastAPI)
```powershell
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
API Documentation & Swagger: `http://127.0.0.1:8000/docs`  
Diagnostics & Telemetry: `http://127.0.0.1:8000/api/diagnostics`

### Start Frontend (Vite + React)
```powershell
cd frontend
npm run dev
```
Local Web Studio: `http://localhost:5173/`

### Run Complete Test Suite
```powershell
pytest backend/tests/test_vectorforge.py -v
```
*All 23 unit and integration tests must pass.*

---

## 5. Conversation Memory & Historical Context

- **Complete Chat Transcript**: See [`md/CHAT_TRANSCRIPT.md`](md/CHAT_TRANSCRIPT.md) for the verbatim 175+ turn conversation between user Abid Ali and Antigravity, including every design debate, visual edge bug, and bug fix.
- **Transcript Updater**: Run `python scripts/export_chat.py` anytime to append latest turns from the Antigravity conversation log.
- **Architectural Brain Document**: See [`md/BRAIN.md`](md/BRAIN.md) for deep technical specifications, data flow diagrams, and OpenCV mathematical pipelines.
- **Version Changelog**: See [`md/CHANGELOG.md`](md/CHANGELOG.md).
- **Feature Roadmap**: See [`md/TODO.md`](md/TODO.md).
