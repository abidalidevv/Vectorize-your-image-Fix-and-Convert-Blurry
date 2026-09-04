# CLAUDE.md — Vectorizer AI Master Architecture & Developer Guide

> **Context for Claude / AI Assistants Auditing or Extending This Codebase**  
> Vectorizer AI (formerly VectorForge AI) is an open-source, local-first raster-to-vector web application designed as a high-fidelity alternative to Vectorizer.io. It runs 100% locally on Windows without external APIs, cloud subscriptions, or API keys.

---

## 1. Environment & Prerequisites

- **Operating System**: Windows 11 / 10 (PowerShell)
- **Python**: 3.14+ (64-bit) at `C:\Users\Abid\AppData\Local\Programs\Python\Python314\python.exe`
- **Node.js**: v24+ with npm
- **Backend Port**: `8000` (FastAPI / Uvicorn)
- **Frontend Port**: `5173` (Vite / React 19)

---

## 2. Quick Start Commands

### Start Backend Server
```powershell
# From repo root
cd c:\Users\Abid\Desktop\vector\vectorforge-ai\backend\app
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```
- Health check: `http://127.0.0.1:8000/health`
- Interactive Swagger docs: `http://127.0.0.1:8000/docs`

### Start Frontend Dev Server
```powershell
# From repo root
cd c:\Users\Abid\Desktop\vector\vectorforge-ai\frontend
npm run dev
```
- Web UI: `http://localhost:5173` (Vite proxies `/api`, `/temp`, `/health` to backend port 8000)

### Run Test Suite
```powershell
# Pytest unit & integration tests (11/11 tests)
cd c:\Users\Abid\Desktop\vector\vectorforge-ai
python -m pytest backend/tests/test_vectorforge.py -v

# End-to-end full HTTP pipeline test
python tests/test_api_e2e.py
```

### Production Build
```powershell
cd c:\Users\Abid\Desktop\vector\vectorforge-ai\frontend
npm run build
```

---

## 3. Core Principles: Vectorization vs. Raster Images

Understanding what vectorization does — and how different types of imagery behave — is fundamental:

### Category A: Flat Graphics, Logos, Icons & Line Art (Optimal)
- **Nature**: Discrete color regions, solid shapes, sharp boundary edges, high contrast.
- **Vector Output**: Mathematical Bézier curves (`<path d="...">`). 100% resolution-independent, razor-sharp at 2000% zoom.
- **Workflow**: Instant 1-click vectorization using the **High** preset. No preprocessing or manual tuning required.
- **Fine Lines & Concentric Circles**: Automatically routed to the **2x Nearest-Neighbor Supersampling Pipeline** (`trace_bw`), preserving 1px lines without notches or intersection webbing.

### Category B: Complex Photographs, Banners & 3D Shaded Typography
- **Nature**: Continuous tone gradients, soft lighting, photographic shadows, JPEG compression noise, and drop-shadows.
- **What Happens if Traced Directly with High Precision**:
  - Vector engines represent every color boundary as a distinct geometric polygon.
  - In continuous-tone photographs or 3D shaded typography, there are hundreds of subtle gradient steps.
  - Tracing raw RGB directly with `color_precision=7` and `layer_difference=12` forces the engine to carve out thousands of micro-polygons (e.g., 5,000+ paths).
  - This results in stepped contour bands (posterization shards) that appear fragmented or jagged.
- **Recommended Workflow for Photographic / Gradient Artwork**:
  1. **Quantization**: Open the **Color Palette** panel and click **Quantize** (set to 4 to 12 colors). This flattens continuous-tone gradients into discrete artistic layers before tracing.
  2. **Preset Selection**: Use **Balanced** or **Fast** preset (which applies higher `filter_speckle` to discard micro-shards).
  3. **Crop / Isolation**: For banners containing photos with overlaid text, crop or isolate the graphic/text elements so photographic noise does not pollute the vectorizer.

---

## 4. End-to-End System Architecture & Data Flow

```
[User Upload (PNG/JPG/WebP/BMP)]
               │
               ▼
   [POST /api/upload] ──► Validates Magic Bytes & Dimensions
               │
               ├──► Creates session in `backend/app/temp_files/<session_id>/`
               │
               ▼
   [POST /api/analyze] ──► Color count, Edge density, Mode recommendation
               │
      ┌────────┴────────────────────────────────────────┐
      ▼                                                 ▼
[Optional: Preprocess]                         [Optional: Quantize]
(Denoise, Contrast, Sharpen)                   (K-Means 2–64 colors)
      │                                                 │
      └────────────────────────┬────────────────────────┘
                               ▼
                    [POST /api/vectorize]
                               │
            ┌──────────────────┴──────────────────┐
            ▼                                     ▼
 [Monochrome Line Art]                   [Color / Graphic Mode]
 (line_detector: 2x NN                   (vtracer: stacked hierarchy,
  supersample, binary cutout)             spline fitting, scour optimize)
            │                                     │
            └──────────────────┬──────────────────┘
                               ▼
                     [Output SVG Generated]
                               │
              ┌────────────────┴────────────────┐
              ▼                                 ▼
   [Interactive Web Preview]           [POST /api/export]
   - Zoom up to 2000%                  - Optimized SVG (Scour)
   - Split Before/After Slider         - High-Res PNG (resvg-py 1x–8x)
   - Layer Color Toggling
```

---

## 5. Backend Component Breakdown (`backend/app/`)

### 1. `main.py`
- FastAPI application entry point.
- Configures CORS middleware allowing `http://localhost:5173` and local origins.
- Mounts static `/temp` route to serve uploaded and generated session files.
- Uses FastAPI `lifespan` context manager to initialize and gracefully clean up temp files.
- Registers all API routers: `upload`, `analyze`, `preprocess`, `quantize`, `vectorize`, `export`.

### 2. `core/session.py` (`SessionManager`)
- Manages ephemeral in-memory session metadata alongside physical directories under `temp_files/<session_id>/`.
- Tracks pipeline stages:
  - `original_path`: Uploaded raster file.
  - `preprocessed_path`: Post-denoise/sharpen image.
  - `quantized_path`: Palette-reduced image.
  - `svg_path`: Final generated SVG vector.
- Handles automated session expiration and disk cleanup.

### 3. `image_processing/line_detector.py`
- **Purpose**: Detects thin delicate lines (1–2px), concentric radar circles, crosshairs, and engineering sketches.
- **Algorithm**:
  - `detect_line_art(img)`: Computes monochrome parity, foreground pixel ratio, and morphological cross-erosion thin line ratio (`thin_line_ratio > 0.15`).
  - `enhance_fine_lines(img, scale=2)`: Uses **2x nearest-neighbor supersampling** (`cv2.INTER_NEAREST`).
  - **Why Nearest-Neighbor**: Avoids morphological dilation or bicubic interpolation, ensuring concentric rings retain 100% 4-quadrant symmetry and crosshairs never produce corner bulging or intersection webbing.

### 4. `image_processing/analyzer.py`
- Computes image complexity metrics:
  - Total unique colors and dominant color palette.
  - Edge density via Canny edge detection.
  - Saturation mean and luminance variance.
  - Recommends optimal tracing mode: `logo`, `illustration`, `sketch`, `bw`, or `photo`.

### 5. `image_processing/preprocessor.py`
- OpenCV-based image conditioning before tracing:
  - Bilateral and Gaussian noise reduction.
  - CLAHE (Contrast Limited Adaptive Histogram Equalization).
  - Unsharp mask sharpening to crisp up blurry raster text glyphs.
  - Thresholding and automatic background color removal.

### 6. `image_processing/quantizer.py`
- Color reduction pipeline:
  - **K-Means Clustering**: Uses OpenCV `cv2.kmeans` to cluster continuous colors into `k` centroids (2 to 64 colors).
  - **Median-Cut**: Alternative box-splitting quantization algorithm.
  - Extracts structured palette swatches with hex codes, RGB values, and pixel coverage percentages.

### 7. `vectorization/vtracer_engine.py` (`VTracerEngine`)
- Primary vectorization engine wrapping the Rust `vtracer` library.
- **Key Methods**:
  - `trace()`: Handles full-color vectorization using `hierarchical="stacked"` to prevent seam gaps and perimeter notches.
  - `trace_bw()`: Handles line art using 2x supersampling, `hierarchical="cutout"`, and automatic background rect injection.
- **Quality Presets**:
  - `fast`: Polygon mode, `color_precision=4`, `layer_difference=24`, `filter_speckle=2`.
  - `balanced`: Spline mode, `color_precision=7`, `layer_difference=16`, `filter_speckle=1`.
  - `high` (Default): Spline mode, `color_precision=7`, `layer_difference=12`, `filter_speckle=1`, `path_precision=6`.
  - `ultra`: Spline mode, `color_precision=8`, `layer_difference=6`, `filter_speckle=0`.

### 8. `vectorization/contour_engine.py` (`ContourEngine`)
- Pure Python/OpenCV fallback engine for monochrome line art.
- Uses `cv2.findContours(cv2.RETR_CCOMP, cv2.CHAIN_APPROX_TC89_KCOS)` with `cv2.approxPolyDP`.
- Generates compound SVG paths with `fill-rule="evenodd"`, ensuring concentric nested rings do not fill as solid black disks.

### 9. `vectorization/engine_selector.py`
- Intelligently routes vectorization requests:
  - If `image_mode == "auto"`, runs `detect_line_art`. If fine line art is detected, routes to `VTracerEngine.trace_bw`.
  - Otherwise, routes to `VTracerEngine.trace` (color mode).
  - Automatically falls back to `ContourEngine` if Rust VTracer encounters an unrecoverable condition.

### 10. `utils/svg_optimizer.py`
- `ensure_viewbox(svg_content)`: Guarantees SVG root contains `viewBox="0 0 W H"` matching width and height.
- `validate_svg(svg_content)`: Uses `lxml.etree` to verify XML well-formedness, counts paths, groups, and unique fill colors.
- `extract_layers_from_svg(svg_content)`: Parses distinct fill colors and builds the layer tree for UI toggling.
- `optimize_svg(svg_content)`: Runs `scour` to strip redundant XML metadata, formatting whitespace, and unneeded tags.

### 11. `export/png_exporter.py` & `export/svg_exporter.py`
- High-fidelity raster export via `resvg_py` (Rust-based SVG renderer).
- Supports 1x, 2x, 4x, and 8x scale multipliers (rendering crisp PNGs up to 16,000px without blur).
- Supports transparent or custom background fills.

---

## 6. Frontend Component Breakdown (`frontend/src/`)

### 1. `store/appStore.ts` (Zustand)
- Centralized reactive state store managing:
  - `sessionId`, `stage` (`idle`, `uploading`, `analyzing`, `quantizing`, `vectorizing`, `exporting`, `error`).
  - `imageInfo` and `analysisResult`.
  - `preprocessSettings`, `vectorizeSettings`, and `numColors`.
  - `viewMode` (`original`, `enhanced`, `vector`) and `showSplitView`.
  - `zoom` (0.05x to 20x) and `pan` offset coordinates.
  - `layers` array with visibility toggling.

### 2. `components/PreviewCanvas.tsx`
- Interactive viewport supporting smooth focal-point zoom (up to 2000%) and pan dragging.
- **Non-Passive Wheel Listener**:
  - Attached with `{ passive: false }` to intercept `e.preventDefault()`, completely preventing browser page zoom when users scroll or pinch on the canvas.
- **Split View**:
  - Draggable center divider comparing before and after.
  - **Left Side**: Original source image.
  - **Right Side**: Vector SVG output.
  - Features floating indicators (`Original` and `Vector Output`) so users instantly understand the comparison.
  - Toolbar buttons automatically synchronize with the split state.

### 3. `components/LeftPanel.tsx`
- Accordion studio controls for:
  - **Image Mode**: Auto, Logo, Photo, Sketch, B&W.
  - **Quality Preset**: Fast, Balanced, High, Ultra.
  - **Color Quantization**: Palette slider (2–64 colors) and one-click "Quantize" action.
  - **Advanced Tracing Sliders**: Filter speckle, color precision, layer difference, corner threshold, length threshold.
  - **One-Click "◈ Vectorize" Action Button**.

### 4. `components/RightPanel.tsx`
- **Vector Stats**: Path count, color count, file size, dimensions.
- **Layer Manager**: Displays color swatches, hex codes, path counts per color, and toggle switches to show/hide individual SVG layers in real time.

### 5. `components/TopBar.tsx`
- Top header with logo, file upload trigger, reset button, and export action.
- **Downward-Oriented Tooltips**: Configured to render downwards (`top: calc(100% + 8px)`) to prevent top-edge clipping in desktop viewports.

### 6. `components/ExportModal.tsx`
- Dialog modal for downloading:
  - **SVG**: Cleaned, scour-optimized scalable vector file.
  - **PNG**: Rendered via `resvg` with scale multipliers (1x, 2x, 4x, 8x) and background choice (transparent or solid).

### 7. `index.css`
- Bespoke modern dark glassmorphism design system:
  - Curated color tokens (`--bg-primary`, `--accent-primary`, `--border-default`, etc.).
  - Responsive layout media queries (`> 1080px` 3-column, `<= 820px` mobile segmented tabs, `<= 460px` compact header).

---

## 7. Critical Technical Constraints (Must-Follow Rules)

### Rule 1: `vtracer` Positional Arguments Only (CRITICAL)
In `vtracer` 0.6.x on Windows Python 3.14, calling `convert_image_to_svg_py` with keyword arguments crashes with a PyO3 tuple parsing panic.  
**Always pass exactly 13 positional arguments in order:**
```python
vtracer.convert_image_to_svg_py(
    str(image_path),        # 1: input path
    str(output_svg_path),   # 2: output path
    colormode,              # 3: "color" or "binary"
    hierarchical,           # 4: "stacked" or "cutout"
    mode,                   # 5: "spline", "polygon", "pixel"
    filter_speckle,         # 6: int
    color_precision,        # 7: int (1-8)
    layer_difference,       # 8: int
    corner_threshold,       # 9: int (degrees)
    length_threshold,       # 10: float
    max_iterations,         # 11: int
    splice_threshold,       # 12: int
    path_precision,         # 13: int
)
```

### Rule 2: Always Use `hierarchical="stacked"` for Color Images
- In `cutout` mode, separate path fitting creates micro-gaps between adjacent polygons. Against dark canvas backgrounds, these appear as **black triangular wedges**.
- In `stacked` mode, lower color layers form continuous foundations, guaranteeing zero seam gaps, smooth circular arcs, and clean color transitions.

### Rule 3: Always Use 2x Nearest-Neighbor for Fine Line Art
- Do not apply morphological dilation or Gaussian blur to 1px line drawings. It causes line pinching at crosshairs and triangle webbing at intersections.
- The 2x nearest-neighbor supersampling pipeline cleanly doubles the coordinate space, enabling Rust VTracer to preserve 100% circularity and symmetry.

### Rule 4: Always Inject SVG `viewBox`
- VTracer emits `<svg width="W" height="H">` without a `viewBox`.
- Always pass output SVGs through `ensure_viewbox(svg_content)` to inject `viewBox="0 0 W H"`. Without this, SVGs will clip or scale incorrectly when embedded in responsive HTML or canvas views.

### Rule 5: Use `resvg_py` for PNG Export
- Never use `cairosvg` on Windows (requires external GTK DLLs).
- Use `resvg_py.svg_to_bytes(svg_string=..., zoom=scale, background=...)`.

---

## 8. Audit & Verification Checklist for Claude

When auditing or reviewing changes to this codebase, execute the following verification steps:

```powershell
# 1. Run full backend pytest suite (all 11 tests must pass)
cd c:\Users\Abid\Desktop\vector\vectorforge-ai
python -m pytest backend/tests/test_vectorforge.py -v

# 2. Run end-to-end HTTP pipeline test
python tests/test_api_e2e.py

# 3. Verify frontend production TypeScript build
cd frontend
npm run build
```

### Manual Verification Checks
1. **Concentric Circles**: Upload a circle radar target with crosshairs -> Vectorize -> Verify in Split View at 300%+ zoom that circles are smooth, complete, and crosshair intersections have zero black webbing or severed lines.
2. **Text / Logo Graphics**: Upload a logo with text -> Vectorize -> Check that interior letter holes (e.g., 'O', 'A', 'P') are carved out cleanly via compound paths.
3. **Photographic Artwork**: For images with gradients or drop shadows, verify that running **Quantize** (4–8 colors) before vectorizing produces clean artistic vector planes rather than thousands of fragmented polygon shards.
4. **Canvas Zooming**: Scroll mouse wheel over the preview canvas -> Verify only the canvas zooms and the outer browser page does not scale.
5. **Tooltips**: Hover over TopBar buttons (`Upload`, `Reset`, `⬇ SVG`, `⬇ PNG`) -> Verify tooltips render downward and remain fully on-screen.
