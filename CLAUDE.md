# CLAUDE.md — Vectorizer AI Developer & Agent Guide

> **Context for Claude / AI Assistants working on this codebase**  
> Vectorizer AI is a production-quality, local-first raster-to-vector web application designed as an open-source alternative to Vectorizer.io. It runs 100% locally on Windows without requiring external APIs, cloud subscriptions, or API keys.

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
- Web UI: `http://localhost:5173` (proxies `/api`, `/temp`, `/health` to backend on port 8000)

### Run Tests
```powershell
# Pytest unit & integration tests
cd c:\Users\Abid\Desktop\vector\vectorforge-ai
python -m pytest backend/tests/test_vectorforge.py -v

# End-to-end full pipeline HTTP test
python tests/test_api_e2e.py
```

### Build Frontend
```powershell
cd c:\Users\Abid\Desktop\vector\vectorforge-ai\frontend
npm run build
```

---

## 3. Repository Architecture

```
vectorforge-ai/
├── CLAUDE.md                    # This developer guide
├── README.md                    # User and project overview
├── CHANGELOG.md                 # Version release history
├── TODO.md                      # Roadmap and planned enhancements
├── backend/
│   ├── requirements.txt         # Python dependencies
│   ├── app/
│   │   ├── main.py              # FastAPI app, CORS, routers, lifespan
│   │   ├── core/
│   │   │   ├── config.py        # Settings (pydantic-settings)
│   │   │   └── session.py       # SessionManager (pipeline stages & temp files)
│   │   ├── models/
│   │   │   ├── requests.py      # Pydantic request models
│   │   │   └── responses.py     # Pydantic response models
│   │   ├── image_processing/
│   │   │   ├── analyzer.py      # Color zones, complexity, edge density, mode recommendation
│   │   │   ├── line_detector.py # Fine line detector & 2x supersampling without corner bulging
│   │   │   ├── preprocessor.py  # Denoise, contrast, sharpen, bilateral filter, grayscale
│   │   │   └── quantizer.py     # K-Means & Median-Cut color quantization & palette builder
│   │   ├── vectorization/
│   │   │   ├── base.py          # AbstractTracer interface
│   │   │   ├── vtracer_engine.py# Primary engine (VTracer Rust wrapper)
│   │   │   ├── contour_engine.py# Fallback B&W engine (OpenCV contours)
│   │   │   └── engine_selector.py# Routes requests to appropriate engine
│   │   ├── export/
│   │   │   ├── svg_exporter.py  # SVG export with scour optimization
│   │   │   └── png_exporter.py  # PNG export with resvg-py (Rust renderer)
│   │   ├── utils/
│   │   │   ├── file_utils.py    # Magic-byte MIME validation & temp management
│   │   │   └── svg_optimizer.py # viewBox injection, layer extraction, scour
│   │   └── api/routes/
│   │       ├── upload.py        # POST /api/upload
│   │       ├── analyze.py       # POST /api/analyze
│   │       ├── preprocess.py    # POST /api/preprocess
│   │       ├── quantize.py      # POST /api/quantize
│   │       ├── vectorize.py     # POST /api/vectorize, GET /api/svg/{id}
│   │       └── export.py        # POST /api/export/svg, POST /api/export/png
│   └── tests/
│       └── test_vectorforge.py  # Pytest suite
├── frontend/
│   ├── package.json             # React 19, Zustand, Axios, Lucide-React
│   ├── vite.config.ts           # Dev server + backend proxy
│   ├── tsconfig.json            # React-JSX bundler config
│   ├── src/
│   │   ├── main.tsx             # React entry point
│   │   ├── App.tsx              # Shell layout + modal overlays
│   │   ├── index.css            # Dark glassmorphism design system
│   │   ├── store/
│   │   │   └── appStore.ts      # Global Zustand state management
│   │   ├── api/
│   │   │   └── client.ts        # Axios API client
│   │   └── components/
│   │       ├── TopBar.tsx       # Mode switch, file name, export actions
│   │       ├── DropZone.tsx     # Drag-and-drop & clipboard paste
│   │       ├── PreviewCanvas.tsx# Zoom (up to 2000%), pan, split slider (isolated canvas zoom)
│   │       ├── LeftPanel.tsx    # Preprocessing, quantization, tracing controls
│   │       ├── RightPanel.tsx   # Color palette, layer toggling, SVG stats
│   │       ├── ExportModal.tsx  # SVG/PNG multi-scale export modal dialog
│   │       └── StatusBar.tsx    # Zoom level, dimensions, engine status
├── samples/                     # Test images (PNG, B&W, logo, transparent)
└── tests/
    └── test_api_e2e.py          # Python E2E API test runner
```

---

## 4. Critical Technical Gotchas & Rules

### 1. `vtracer` Call Signature (CRITICAL)
In `vtracer` 0.6.x (compiled with PyO3 for Python 3.14 on Windows), calling `convert_image_to_svg_py` with keyword arguments causes a PyO3 tuple parsing panic.  
**Always call it with positional arguments:**
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
    corner_threshold,       # 9: int (degrees, e.g. 60)
    length_threshold,       # 10: float (e.g. 4.0)
    max_iterations,         # 11: int (e.g. 10)
    splice_threshold,       # 12: int (e.g. 45)
    path_precision,         # 13: int (decimal places)
)
```

### 2. High-Fidelity SVG Rasterization (`resvg-py`)
Do not use `cairosvg` on Windows because it requires external GTK/cairo C libraries.  
Instead, `resvg-py` is installed and used. It is a self-contained Rust engine providing pixel-perfect SVG rendering at arbitrary zoom factors:
```python
import resvg_py
png_bytes = resvg_py.svg_to_bytes(
    svg_string=svg_content,
    zoom=float(scale),
    background=background_color,
)
```

### 3. SVG `viewBox` Attribute
VTracer generates `<svg width="W" height="H">` without a `viewBox`.  
Always pass SVG content through `utils.svg_optimizer.ensure_viewbox(svg_content)` before saving or returning. This adds `viewBox="0 0 W H"`, which is mandatory for responsive scaling and 2000% crisp browser rendering without clipping.

### 4. Fine Line & Concentric Circle Preservation (CRITICAL)
- 1-pixel lines (radar rings, concentric circles, technical sketches) have zero area in polygonal tracing.
- If `filter_speckle > 0`, VTracer treats them as speckle noise and removes them.
- If `hierarchical == "stacked"`, background white polygons paint over thin lines in painter's order.
- In `vtracer` binary mode, polygon inversion can cause the entire canvas to fill as a solid black rectangle.
- **Rules for line art & drawings**:
  1. Use `line_detector.py` to detect and reinforce thin lines orthogonally (`cv2.MORPH_CROSS` 3x3) so they attain a stable 2D manifold without rounding sharp corners.
  2. Always trace with `hierarchical="cutout"` so background patches are carved out around the lines.
  3. Set `filter_speckle=0` and `length_threshold <= 2.0`.
  4. In `ContourEngine`, always use `cv2.RETR_CCOMP` with compound SVG paths (`fill-rule="evenodd"`) so nested concentric shapes never fill as solid black disks.

### 5. Pydantic Settings
Settings are declared using `pydantic_settings.BaseSettings` (not `pydantic.BaseSettings` which was removed in Pydantic v2).

### 6. Frontend Imports
All component imports in `frontend/src/components/*.tsx` import from `../store/appStore` and `../api/client` (single `../`, not double `../../`).

---

## 5. Pipeline Stages

1. **Upload**: Validates magic bytes (PNG, JPG, BMP, WebP) and dimensions (up to 4096×4096). Creates session folder in `temp_files/<session_id>/`.
2. **Analyze**: Computes edge density, color variance, unique color zones, and recommends mode (`logo`, `illustration`, `sketch`, `bw`, `photo`).
3. **Preprocess**: OpenCV pipeline: bilateral/Gaussian denoise, CLAHE contrast enhancement, unsharp mask sharpening, thresholding, grayscale conversion.
4. **Quantize**: K-Means clustering or Median-Cut algorithm to reduce colors to 2–64 discrete tones. Returns structured palette with RGB, hex, and coverage percentages.
5. **Vectorize**:
   - `VTracerEngine`: Rust spline fitting for smooth Bezier curves.
   - `ContourEngine`: OpenCV `findContours` + `approxPolyDP` fallback for monochrome artwork.
6. **Export**:
   - SVG: Cleans with `scour` (removes redundant metadata while preserving viewBox and paths).
   - PNG: Renders via `resvg` at 1x, 2x, 4x, 8x with transparent or custom background.

---

## 6. How to Extend

- **Add a new vectorizer engine**: Inherit from `AbstractTracer` in `vectorization/base.py`, implement `trace()`, and register it in `engine_selector.py`.
- **Add custom preset**: Update `QUALITY_PRESETS` in `vtracer_engine.py` and the corresponding frontend presets in `LeftPanel.tsx`.
- **Add export formats**: Extend `export/` with EPS or PDF exporters (ReportLab can render `resvg` PNGs or convert SVG directly to PDF).

---

## 7. Frontend Responsive Architecture & Tooltip System

### Responsive Layout Strategy
The web UI dynamically adapts across three primary screen tiers:
1. **Desktop (> 1080px)**:
   - Full 3-column studio layout: `LeftPanel` (280px) | `PreviewCanvas` (flex: 1) | `RightPanel` (260px).
   - All sidebars and canvas are concurrently visible.
2. **Laptop & Tablet Landscape (821px – 1080px)**:
   - Adaptive panel widths (`LeftPanel`: 245px, `RightPanel`: 225px) allowing the center canvas 350px–610px of interactive space.
3. **Tablet Portrait & Mobile (<= 820px)**:
   - Sidebars are encapsulated inside `.responsive-panel-wrapper`.
   - A segmented mobile workspace tab bar renders below the TopBar:
     - `🎛 Controls`: Expands `LeftPanel` to 100% viewport width for configuring sliders and tapping `◈ Vectorize`.
     - `👁 Canvas`: Expands `PreviewCanvas` to 100% viewport width with full zoom, pan, and split-view controls.
     - `🎨 Layers`: Expands `RightPanel` to 100% viewport width to view swatches and toggle layer visibility.
   - Auto-switches to `Canvas` tab upon image upload or vectorization completion for immediate visual feedback.
   - Eliminates horizontal window scrolling and layout squishing.

### Breakpoints Table
| Breakpoint | Target Devices | Layout Adjustments |
|---|---|---|
| `> 1080px` | Desktop / Wide Monitors | Standard 3-column layout (280px / flex:1 / 260px) |
| `821px – 1080px` | Small Laptops / Tablets | Compressed 3-column layout (245px / flex:1 / 225px) |
| `<= 820px` | Tablets / Large Phones | Segmented tabs (`Controls`, `Canvas`, `Layers`) with 100% width active panel |
| `<= 640px` | Phones (Portrait) | Compact TopBar (48px), hides PNG scale multipliers, hides non-essential status items |
| `<= 460px` | Small Phones | Icon-only logo `[V]` and upload button `⬆` to prevent header overflow |

### Tooltip Positioning Rules
- **Problem**: Elements near the top edge of the browser viewport (like `TopBar` buttons) have their tooltips hidden/clipped when positioned above (`bottom: calc(100% + 6px)`).
- **Solution**:
  - All `.topbar [data-tooltip]::after` and elements with `[data-tooltip-pos="bottom"]` render **downward** (`top: calc(100% + 8px); bottom: auto;`).
  - Elements on the far right (e.g. `TopBar` export actions) use `[data-tooltip-align="right"]` with `left: auto; right: 0; transform: none;` to avoid overflowing beyond the right viewport margin.
  - Styled with high-contrast dark elevated background (`var(--bg-elevated)`), crisp border (`var(--border-strong)`), `z-index: 9999`, and smooth opacity transition.

---

## 8. Verification & Quality Assurance Checklist

Always verify these after making changes:
```powershell
# 1. Backend Pytest suite (9 tests)
python -m pytest backend/tests/test_vectorforge.py -v

# 2. End-to-end HTTP pipeline test
python tests/test_api_e2e.py

# 3. Frontend production build
cd frontend
npm run build
```
- Browser check at `http://localhost:5173/`:
  - Upload image -> check instant preview.
  - Hover over TopBar buttons (`Upload`, `Reset`, `⬇ SVG`, `⬇ PNG`, `2x`, `4x`, `8x`) -> verify tooltip renders downwards and remains fully visible.
  - Resize browser window from 1280px down to 768px and 480px -> verify mobile tabs work smoothly with zero horizontal overflow.

