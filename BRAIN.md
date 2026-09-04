# 🧠 Vectorizer AI — Brain & Architectural Memory

> **System Memory Bank, Technical Blueprint & Agent Hand-off Guide**  
> **Author**: [Abid Ali](https://abidalidev.com) • [GitHub (@abidalidevv)](https://github.com/abidalidevv) • **Repository**: [Vectorize-your-image-Fix-and-Convert-Blurry](https://github.com/abidalidevv/Vectorize-your-image-Fix-and-Convert-Blurry)  
> **Version**: `1.0.3` • **Status**: Production-Ready, Verified & Tested 100% Locally

---

## 1. Executive Summary & Purpose

**Vectorizer AI** is a local-first, free, and open-source raster-to-vector studio designed as a Windows-native alternative to cloud services like Vectorizer.io. It converts raster images (PNG, JPG, BMP, WebP) into pure, scalable Bézier curve SVG vector paths without relying on external cloud APIs, telemetry, or paid subscriptions.

---

## 2. Core Architecture & Component Map

```
vectorforge-ai/
├── BRAIN.md                       # This Master Architecture & Memory Document
├── CLAUDE.md                      # Developer & AI Assistant Quick-Start Guide
├── README.md                      # GitHub Repository Presentation & Quick Start
├── CHANGELOG.md                   # Detailed Version History & Release Notes
├── TODO.md                        # Task Tracking & Feature Roadmap
├── LICENSE                        # MIT License (Abid Ali)
│
├── backend/                       # Python 3.14+ (FastAPI + OpenCV + VTracer + resvg-py)
│   ├── requirements.txt           # Python Package Dependencies
│   ├── app/
│   │   ├── main.py                # FastAPI Application, CORS Middleware, Lifecycle Events
│   │   ├── core/
│   │   │   ├── config.py          # Pydantic-Settings Configuration (CORS, upload limits)
│   │   │   └── session.py         # SessionManager (session UUID directory isolation)
│   │   ├── models/
│   │   │   ├── requests.py        # Pydantic Schemas for Request Payloads
│   │   │   └── responses.py       # Pydantic Schemas for Response Payloads
│   │   ├── image_processing/
│   │   │   ├── analyzer.py        # Edge density (Sobel), color variance, auto-mode selector
│   │   │   ├── line_detector.py   # Fine line detector & orthogonal line reinforcement (1-2px)
│   │   │   ├── preprocessor.py    # Denoise, CLAHE contrast, sharpen, bg removal, cleanup
│   │   │   └── quantizer.py       # K-Means clustering, Median-Cut, palette extractor
│   │   ├── vectorization/
│   │   │   ├── base.py            # AbstractTracer Interface class
│   │   │   ├── vtracer_engine.py  # Primary Engine: Rust VTracer wrapper (cutout hierarchy)
│   │   │   ├── contour_engine.py  # Fallback Engine: OpenCV RETR_CCOMP + compound paths
│   │   │   └── engine_selector.py # Dynamic engine dispatcher with auto line-art detection
│   │   ├── export/
│   │   │   ├── svg_exporter.py    # Scour SVG optimizer & file saver
│   │   │   └── png_exporter.py    # resvg-py multi-scale raster renderer (1x, 2x, 4x, 8x)
│   │   ├── utils/
│   │   │   ├── file_utils.py      # Magic-byte MIME type validator & temp file manager
│   │   │   └── svg_optimizer.py   # viewBox injector, SVG layer parser, Scour cleaner
│   │   └── api/routes/
│   │       ├── upload.py          # POST /api/upload
│   │       ├── analyze.py         # POST /api/analyze
│   │       ├── preprocess.py      # POST /api/preprocess
│   │       ├── quantize.py        # POST /api/quantize
│   │       ├── vectorize.py       # POST /api/vectorize, GET /api/svg/{session_id}
│   │       └── export.py          # POST /api/export/svg, POST /api/export/png
│   └── tests/
│       └── test_vectorforge.py    # Pytest Unit & Integration Test Suite (10 Tests)
│
├── frontend/                      # React 19 + TypeScript + Vite + Zustand
│   ├── package.json               # Frontend Dependencies & Scripts
│   ├── vite.config.ts             # Dev Server & Reverse Proxy (/api -> 127.0.0.1:8000)
│   ├── tsconfig.json              # TypeScript Strict Compiler Options
│   ├── src/
│   │   ├── main.tsx               # Application Entry Point
│   │   ├── App.tsx                # Main Layout, Paste Listener, Processing Overlay, Tabs
│   │   ├── index.css              # Dark Glassmorphism Design System & Media Queries
│   │   ├── store/
│   │   │   └── appStore.ts        # Zustand Global State Management
│   │   ├── api/
│   │   │   └── client.ts          # Axios API Client & Typed Endpoints
│   │   └── components/
│   │       ├── TopBar.tsx         # Logo, Upload, Reset, SVG/PNG Export & Scale Multipliers
│   │       ├── DropZone.tsx       # Drag-and-drop & clipboard paste file drop target
│   │       ├── PreviewCanvas.tsx  # Deep Zoom (2000%), Pan, Before/After Split Slider
│   │       ├── LeftPanel.tsx      # Preprocessing, Quantization, and Vectorizing Sliders
│   │       ├── RightPanel.tsx     # Color Swatches, SVG Layers Toggling, Stats
│   │       └── StatusBar.tsx      # Dimensions, Zoom %, Path count, Engine status
│
├── docs/                          # Technical Documentation & Assets
│   └── screenshots/               # High-Resolution UI Visuals
├── samples/                       # Test Images (Logos, Icons, Line Art, Transparent PNGs)
└── tests/
    └── test_api_e2e.py            # Python E2E HTTP Test Suite
```

---

## 3. Data Flow & Pipeline Stages

```
[User Image]
     │
     ▼ (POST /api/upload)
[Session Isolation] ─── Validates Magic Bytes (PNG/JPG/BMP/WebP) & Max Dimensions
     │
     ▼ (POST /api/analyze)
[Analyzer] ──────────── Detects Edge Density, Color Variance, Mode ('logo'|'illustration'|'bw'|...)
     │
     ├──► (Optional POST /api/preprocess) ─── Denoise, CLAHE Contrast, Sharpen, BG Removal
     │
     ├──► (Optional POST /api/quantize) ───── K-Means / Median-Cut (2 to 64 discrete colors)
     │
     ▼ (POST /api/vectorize)
[Engine Selector]
     ├──► [VTracer Engine] ──── High-order Bézier spline fitting through color regions
     └──► [Contour Engine] ──── OpenCV findContours + approxPolyDP for binary line art
     │
     ▼
[SVG Optimizer] ────────────── Injects standard viewBox="0 0 W H", extracts color layers
     │
     ├──► (POST /api/export/svg) ── Scour optimization (strips bloat while preserving paths)
     └──► (POST /api/export/png) ── resvg-py Rust rasterizer (1x, 2x, 4x, 8x high-res)
```

---

## 4. Critical Technical Knowledge & Gotchas

### 1. `vtracer` Call Signature on Windows (PyO3 Strictness)
- In `vtracer` 0.6.x on Windows under Python 3.14, invoking `convert_image_to_svg_py` with keyword arguments raises a PyO3 tuple parsing panic.
- **Rule**: ALWAYS pass arguments as positional tuples in exact order:
  ```python
  vtracer.convert_image_to_svg_py(
      str(input_path),        # 1: Input image file path
      str(output_path),       # 2: Output SVG file path
      colormode,              # 3: 'color' or 'binary'
      hierarchical,           # 4: 'stacked' or 'cutout'
      mode,                   # 5: 'spline', 'polygon', 'pixel'
      filter_speckle,         # 6: int
      color_precision,        # 7: int (1-8)
      layer_difference,       # 8: int
      corner_threshold,       # 9: int (degrees)
      length_threshold,       # 10: float
      max_iterations,         # 11: int
      splice_threshold,       # 12: int
      path_precision,         # 13: int (decimal precision)
  )
  ```

### 2. Standalone SVG Rasterization without Cairo (`resvg-py`)
- Standard Cairo/GTK bindings on Windows require complex external DLL installs.
- VectorForge AI uses `resvg-py`, a self-contained Rust engine providing pixel-perfect SVG rendering at high zoom multipliers (1x, 2x, 4x, 8x) without external C libraries.

### 3. SVG `viewBox` Attribute Injection
- VTracer emits `<svg width="W" height="H">` lacking a `viewBox` attribute.
- Without `viewBox`, browsers clip SVGs during CSS scaling and high-zoom rendering.
- `app/utils/svg_optimizer.py` implements `ensure_viewbox(svg_content)`, guaranteeing `viewBox="0 0 W H"` is present in all emitted SVGs.

### 4. Tooltip Positioning Inside Viewport
- TopBar buttons reside at `y ≈ 10px`. Standard CSS tooltips positioned above (`bottom: calc(100% + 6px)`) render offscreen at `y = -15px`.
- `.topbar [data-tooltip]::after` and `[data-tooltip-pos="bottom"]` enforce `top: calc(100% + 8px); bottom: auto;`, guaranteeing all header tooltips open downward inside the viewport.
- Buttons on the right margin use `[data-tooltip-align="right"]` to prevent horizontal clipping.

### 5. IPv4 Proxying in Vite
- Node.js 18+ resolves `localhost` to IPv6 `::1` before IPv4 `127.0.0.1`.
- To prevent proxy connection drops, `vite.config.ts` targets explicit IPv4 `http://127.0.0.1:8000`.

### 6. Line Intersection Bulge Prevention (2× Bicubic Supersampling)
- Morphological dilation (`cv2.dilate`) on thin lines causes cross/T-junctions and concentric circles to fill corner wedges, producing ugly trumpet-shaped webbing after spline curve fitting.
- **Fix in v1.0.3**: Replaced dilation with 2× bicubic supersampling in `line_detector.py`. The tracer operates on the supersampled image and the resulting SVG applies `<g transform="scale(0.5)">` with the original `viewBox="0 0 W H"`. This preserves orthogonal 90° intersections, true circular geometry, and zero junction flaring.

### 7. Canvas Zoom Isolation (Native Non-Passive Wheel Listener)
- In React 19, synthetic `onWheel` registers as passive in modern browsers, ignoring `e.preventDefault()`. When users zoom deeply or pinch, the entire Chrome window zooms and controls clip outside the screen.
- **Fix in v1.0.3**: Attached a native DOM listener on `containerRef.current` with `{ passive: false }` and `e.preventDefault()`. Zoom is strictly isolated to the canvas image and focal-point centered around the mouse cursor.

---

## 5. What is 100% COMPLETE & WORKING ✅

| Feature | Status | Verification Detail |
|---|:---:|---|
| **Image Upload** | ✅ | PNG, JPG, JPEG, BMP, WebP validation up to 4096×4096 px |
| **Complexity Analysis** | ✅ | Edge density, unique color zone detection, auto-mode recommendation |
| **Preprocessing Suite** | ✅ | Bilateral denoise, CLAHE contrast, unsharp mask, bg-removal |
| **Quantization** | ✅ | K-Means & Median-Cut (2 to 64 colors) with palette percentages |
| **VTracer Spline Tracing** | ✅ | Pure Bézier curves, zero pixelation at 2000% zoom |
| **Junction Webbing Prevention** | ✅ | 2× supersampling prevents corner bulging at line intersections |
| **Contour Fallback** | ✅ | OpenCV findContours for pure monochrome / sketch art |
| **Layer Extraction** | ✅ | Parses color groups and provides interactive visibility toggle |
| **Isolated Canvas Zoom** | ✅ | Smooth focal-point zoom (5% to 2000%) without page zoom |
| **Export Modal & Quick Export**| ✅ | Modal with SVG code copy/download & PNG (1x, 2x, 4x, 8x / 300 DPI) |
| **Optimal Default Settings** | ✅ | High quality preset, speckle: 0, lengthThreshold: 2.0 out of the box |
| **Responsive Studio** | ✅ | Desktop 3-column, tablet adaptive, mobile segmented tabs (`Controls`, `Canvas`, `Layers`) |
| **Downward Tooltips** | ✅ | Never clipped above browser window; right-aligned on edge buttons |
| **Automated Tests** | ✅ | 10/10 Pytest unit tests pass, E2E HTTP test suite passes, frontend build compiles in <400ms |

---

## 6. What REMAINS & FUTURE ROADMAP (What to build next) 🚀

The following features represent natural evolutions for future update cycles:

### 1. Batch Processing Mode
- **Goal**: Allow users to drag a folder or multi-select 20+ images and vectorize them in a background queue.
- **Implementation Path**:
  - Add `POST /api/batch/vectorize` endpoint using FastAPI background tasks or `asyncio.Queue`.
  - Add a "Batch Queue" tab in the frontend displaying file progress bars and a "Download All (ZIP)" button.

### 2. Desktop Standalone Executable (Tauri / Electron)
- **Goal**: Package VectorForge AI into a single `.exe` installer for Windows without requiring Python or Node to be pre-installed.
- **Implementation Path**:
  - Use **Tauri** (Rust) or **PyInstaller + Electron** to bundle the FastAPI backend and static Vite frontend into a native Windows window.

### 3. Direct Vector EPS & PDF Export
- **Goal**: Provide direct export to Adobe Illustrator EPS and vector PDF.
- **Implementation Path**:
  - Integrate `cairosvg` or a pure Python SVG-to-PDF/EPS converter (e.g. `svglib` or `reportlab`) to allow graphic designers to open files directly in CorelDraw or Illustrator.

### 4. AI Deep-Learning Line Inpainting (Edge Reconnect)
- **Goal**: Repair broken or degraded line drawings before vectorization.
- **Implementation Path**:
  - Add a lightweight ONNX model (e.g., informative-drawings or morphological skeleton repair) as an optional neural preprocessing step.

### 5. Client-Side WebAssembly (WASM) Tracing
- **Goal**: Compile `vtracer` to WebAssembly (`wasm-bindgen`) to execute vectorization directly inside the browser client without any backend server.
- **Implementation Path**:
  - Build `vtracer` Rust crate to WASM and bundle in Vite for serverless deployment on GitHub Pages or Vercel.

---

## 7. Instructions for Claude / Future AI Developers

When continuing or extending VectorForge AI:
1. **Always run tests first**:
   ```powershell
   python -m pytest backend/tests/test_vectorforge.py -v
   python tests/test_api_e2e.py
   cd frontend && npm run build
   ```
2. **Preserve VTracer positional call**:
   - Never use keyword arguments (`input_path=...`) when calling `vtracer.convert_image_to_svg_py`.
3. **Always ensure `viewBox`**:
   - Any new engine must pass generated SVG through `utils.svg_optimizer.ensure_viewbox()`.
4. **Maintain Responsive Tab System**:
   - Sidebars live in `.responsive-panel-wrapper` controlled by `appStore.ts` `mobileTab` state.
   - Do not break the `@media (max-width: 820px)` tabbed layout.
5. **Keep Tooltips Positioned Downward**:
   - Any new buttons placed in `TopBar` must specify `data-tooltip-pos="bottom"`.
