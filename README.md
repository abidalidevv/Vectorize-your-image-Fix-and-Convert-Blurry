# ⚡ Vectorizer AI

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.14+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React 19](https://img.shields.io/badge/React-19.0-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Rust Engine](https://img.shields.io/badge/VTracer-Rust%20Engine-DEA584?style=for-the-badge&logo=rust&logoColor=black)](https://github.com/visioncortex/vtracer)
[![Pytest](https://img.shields.io/badge/Pytest-23%2F23%20Passed-brightgreen?style=for-the-badge&logo=pytest&logoColor=white)](backend/tests/test_vectorforge.py)
[![Version](https://img.shields.io/badge/Version-1.2.0%20Pro-blueviolet?style=for-the-badge)](md/CHANGELOG.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)
[![Author](https://img.shields.io/badge/Author-Abid%20Ali-blueviolet?style=for-the-badge&logo=google-chrome&logoColor=white)](https://abidalidev.com)
[![GitHub Profile](https://img.shields.io/badge/GitHub-abidalidevv-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/abidalidevv)

**Fix blurry logos, icons, and illustrations. Convert low-res raster images into crisp, infinitely scalable vector graphics (SVG) — 100% locally on your machine.**

[Explore Features](#-key-features) • [Quick Start](#-quick-start-guide) • [Live Diagnostics](docs/diagnose.html) • [Master Docs](docs/documentation.html) • [Architecture](#-architecture) • [API Reference](#-api-endpoints) • [Documentation Hub](md/README.md) • [Portfolio](https://abidalidev.com)

</div>

---

## 🖼️ Visual Showcase

### 🖥️ Full Studio — Raster Image Loaded & Interactive Canvas
![Studio with Loaded Image](docs/screenshots/studio-original.png)

### 🔍 2000% Deep Zoom — Pure Scalable Bézier Curves (Zero Pixelation)
![2000% Zoom Vector Result](docs/screenshots/vector-2000-zoom.png)

### 🎛️ Studio Modules & Feature Breakdown
<div align="center">
  <img src="docs/screenshots/image-info-ai.png" width="31%" alt="AI Mode Recommendation" />
  <img src="docs/screenshots/quantize-controls.png" width="31%" alt="Preprocessing & Quantization" />
  <img src="docs/screenshots/tracing-settings.png" width="31%" alt="Spline Tracing Controls" />
</div>

<br />

<div align="center">
  <img src="docs/screenshots/drop-zone.png" width="48%" alt="Empty Studio Drop Zone" />
  <img src="docs/screenshots/vector-stats.png" width="48%" alt="Vector Statistics & Validation" />
</div>

---

## 💡 Why Vectorizer AI?

Online services like **Vectorizer.io** or subscription-based cloud converters lock vectorization behind paywalls, impose restrictive daily quotas, or transmit sensitive branding and artwork to remote cloud servers.

**Vectorizer AI** provides an open-source, local-first alternative that runs entirely on your own hardware without external API keys or cloud dependencies.

| Feature | Vectorizer AI ⚡ | Vectorizer.io / Cloud Converters ☁️ |
|---|:---:|:---:|
| **Cost & License** | **100% Free & Open Source** (MIT) | Paid Subscription / Pay-per-credit |
| **Privacy & Security** | **100% Local-First** (Zero data leaves device) | Images sent to remote 3rd-party servers |
| **Offline Execution** | ✅ Full offline capability on Windows | ❌ Requires active high-speed internet |
| **Resolution Limit** | ✅ Up to 4096 × 4096 px | ❌ Restricted by tier/credits |
| **Vector Engine** | ✅ High-performance Rust Bézier Engine (VTracer) | Proprietary cloud engine |
| **Color Quantization** | ✅ K-Means Clustering & Median-Cut (2–64 colors) | Fixed server-side palette |
| **SVG Optimization** | ✅ Built-in Scour optimization + standard `viewBox` | Often leaves redundant metadata |
| **PNG Upscaling** | ✅ `resvg` Rust renderer (1×, 2×, 4×, 8×) | Often 1× only or paid extra |

---

## 🚀 Key Features

### 1. Dual Vectorization Engines
- **VTracer Rust Spline Engine**: Fits high-order Bézier curves through color boundaries. Generates buttery-smooth curves without staircasing or visible polygon artifacts.
- **OpenCV Contour Fallback**: High-speed edge contour tracing with `approxPolyDP` simplification for sharp black-and-white logos, technical line art, and typography.
- **Engine Selector**: Automatically selects the best engine based on detected edge density, color count, and image mode.

### 2. Intelligent Pre-Analysis & Mode Recommendation
- Analyzes image complexity using Sobel edge density, color variance, and alpha channel presence.
- Automatically selects the best preset:
  - `Logo / Clipart`: Prioritizes smooth curves, clean color grouping, and low speckle.
  - `Illustration`: Preserves layered color zones and detailed fills.
  - `Sketch / Line Art`: High-contrast thresholding with strict path smoothing.
  - `Black & White`: Crisp binary vectorization without color bleed.
  - `Photo`: High-precision palette clustering for painterly vector art.

### 3. Advanced Image Preprocessing
- **Denoise Filtering**: Bilateral and Gaussian filtering to remove compression artifacts from blurry JPEGs.
- **Contrast & Brightness Tuning**: CLAHE (Contrast Limited Adaptive Histogram Equalization) for dark or low-contrast graphics.
- **Unsharp Mask Sharpening**: Accentuate soft edges before tracing.
- **Connected Background Removal**: Auto-detects background color or lets you sample with adjustable color tolerance.
- **Anti-alias Cleanup**: Binarizes fuzzy boundary pixels for razor-sharp vector cuts.

### 4. Interactive Studio & Canvas
- **Deep Zoom**: Zoom up to **2000%** with zero browser pixelation.
- **Smooth Navigation**: Pan effortlessly with mouse drag or trackpad.
- **Interactive Split Slider**: Drag the split divider to compare original raster vs. vectorized output side-by-side.
- **Interactive Palette**: Inspect detected HEX codes, RGB values, and area percentages.
- **Layer Visibility Toggling**: Show/hide individual color layers directly inside the SVG viewer.

### 5. Multi-Scale Clean Exports
- **SVG Export**: Processed through `scour` to strip redundant tags and enforce standard `viewBox="0 0 W H"` coordinates for web responsiveness.
- **Multi-Scale PNG Export**: Uses `resvg-py` (standalone Rust SVG renderer) to render at 1×, 2×, 4×, and 8× resolutions with transparent or solid background.

### 6. Background Remover Studio (Fast & Ultra Pro Tiers)
- **Fast Tier (`isnet-general-use`, ~178.6MB ONNX)**: General-use boundary segmentation for graphic logos, app icons, and product cutouts (~1.5s–3s CPU).
- **Ultra Tier (`birefnet-general`, ~972.7MB ONNX)**: Bilateral Reference Network for high-resolution dichromatic matting (fine hair, animal fur, transparent glass).
- **Edge Defringe Halo Choke (`cv2.erode`)**: Uses an elliptical morphological structuring element ($k \in [1, 9]$) to physically strip fringe bleeding from original backgrounds.
- **Physical Alpha-Unmixing Color Decontamination**:
  $$\text{true\_fg} = \text{np.clip}\left(\frac{\text{observed} - \text{bg\_color} \cdot (1 - \alpha)}{\alpha}, 0, 255\right)$$
  Inverts optical compositing to eliminate backdrop color bleed in semi-transparent edges ($0.05 < \alpha < 0.95$).
- **Zero-Arena Memory Management**: Configures ONNX Runtime with `enable_cpu_mem_arena = False` and proactive GC to prevent 822MB memory allocation crashes on Windows CPU.
- **Resilient Fallback**: Gracefully falls back to Fast mode without 500 errors if Ultra weights are uncached.

### 7. Image Enhancer Studio (Fast & Ultra Pro Tiers + Face Restoration)
- **Fast Tier (`realesr-general-x4v3`, ~4.9MB ONNX)**: Lightweight neural super-resolution network upscaler + 6-stage classical CV pipeline (~1–2s).
- **Ultra Tier (`RealESRGAN_x4plus`, ~67.1MB ONNX)**: 23-layer Residual-in-Residual Dense Block (RRDBNet) for maximum vector-ready clarity and edge reconstruction.
- **Old Photo & Face Restoration (`GFPGANv1.4`, ~324.5MB ONNX)**:
  - Detects faces with high-precision YuNet landmark detector (<3ms).
  - Performs 512×512 affine similarity alignment to center facial geometry and eye pupils.
  - Neural face reconstruction with Generative Facial Prior GAN.
  - Gaussian radial falloff blending and inverse affine projection preserves original composition.
  - Adjustable **Face Detail Blend (Fidelity)** slider (0.1–1.0).
- **7-Stage Classical Enhancement Pipeline**:
  1. Neural Super-Resolution (x4v3 Fast or x4plus Ultra)
  2. Bilateral Filter (edge-preserving denoising)
  3. CIE-LAB CLAHE (adaptive contrast equalization on $L^*$ channel)
  4. Gaussian High-Pass Unsharp Masking ($I_{\text{sharp}} = 1.5 \cdot I - 0.5 \cdot G_\sigma(I)$)
  5. Morphological Edge Refinement (smoothes boundary stairstepping)
  6. HSV Dynamic Range & Saturation Vibrance Tuning
  7. Optional GFPGAN Face & Eye Restoration

### 8. Magic Eraser & Inpainting Studio (Fast & Pro Tiers)
- **Fast Fourier Convolutions (`LaMa-ONNX`, ~198.4MB ONNX)**: Large Mask Inpainting network trained on high-resolution image textures to synthesize realistic backgrounds.
- **Interactive Canvas Brush Overlay**: Smooth HTML5 canvas layered directly on top of the original image with synchronized zoom, pan, and real-time circular brush cursor.
- **Adjustable Brush Radius**: 5px to 120px brush slider with live preview and quick-select presets (15px, 30px, 50px, 80px).
- **Edge Margin Expansion (Dilation)**: Morphological elliptical dilation removes background halos around removed objects.
- **Pro Edge Gradient Refinement**: Multi-scale bilateral boundary smoothing and seamless color matching.
- **Multi-Level Undo & Clear**: Instant stroke undo and mask clearing.
- **Seamless Export & Handoff**: Jump straight from Inpainting to Vectorizer or Enhancer.

### 9. Live Diagnostics Dashboard (`diagnose.html`)
- Dedicated browser dashboard and `GET /api/diagnostics` endpoint for comprehensive telemetry across all **7 AI & neural models**.
- Audits on-disk neural model weights, byte sizes, ONNX Runtime execution providers (`CPUExecutionProvider`, `CUDAExecutionProvider`, `DmlExecutionProvider`), host RAM load, and active sessions.
- In-browser synthetic probe runner sends live synthetic test rasters to `/health`, `/api/diagnostics`, `/api/remove-bg`, `/api/enhance`, and `/api/inpaint` with latency benchmarking.
- One-click copyable JSON diagnostic report for troubleshooting and GitHub issues.

### 10. Full Mobile & Tablet Responsiveness
- **Desktop (> 1080px)**: 3-column pro studio layout.
- **Medium Screens (821px–1080px)**: Adaptive compact layout.
- **Mobile & Tablet (<= 820px)**: Sleek segmented workspace navigation (`🎛 Controls`, `👁 Canvas`, `🎨 Layers`), giving each view 100% viewport width without horizontal scrolling.
- **Downward Tooltips**: Tooltips open downwards so they never hide or clip outside the top edge of the browser viewport.

---

## 🏗️ Architecture

```
vectorforge-ai/
│
├── backend/                             # Python 3.14+ FastAPI Server
│   ├── app/
│   │   ├── api/routes/                  # REST API Endpoints
│   │   │   ├── upload.py                # Image validation & session storage
│   │   │   ├── analyze.py               # Edge & color complexity analyzer
│   │   │   ├── preprocess.py            # Denoise, contrast, sharpen, bg-removal
│   │   │   ├── quantize.py              # K-Means & Median-Cut color clustering
│   │   │   ├── vectorize.py             # Tracing pipeline & SVG generator
│   │   │   ├── export.py                # SVG optimization & resvg PNG rendering
│   │   │   └── diagnostics.py           # Deep hardware & model telemetry route
│   │   ├── bg_remover/                  # ISNet & BiRefNet matting + defringe choke
│   │   ├── image_enhancer/              # Real-ESRGAN (x4v3 & x4plus) + 6-stage CV
│   │   ├── image_processing/            # Computer vision analysis & quantization
│   │   ├── vectorization/               # VTracer (Rust) & Contour (OpenCV)
│   │   ├── export/                      # Scour SVG & resvg-py PNG exporters
│   │   ├── core/                        # SessionManager & App Settings
│   │   └── main.py                      # FastAPI App initialization & CORS
│   └── tests/
│       └── test_vectorforge.py          # Pytest suite (21/21 passing)
│
├── frontend/                            # React 19 + TypeScript + Vite
│   ├── public/
│   │   ├── documentation.html           # Comprehensive technical master guide
│   │   └── diagnose.html                # Live telemetry & diagnostic dashboard
│   ├── src/
│   │   ├── components/                  # TopBar, Canvas, Left/Right panels
│   │   ├── features/
│   │   │   ├── bg_remover/              # Background Remover Studio Panel
│   │   │   └── enhancer/                # Image Enhancer Studio Panel
│   │   ├── store/appStore.ts            # Zustand global application state
│   │   └── api/client.ts                # Axios REST client
│   └── vite.config.ts                   # Vite config with backend proxy
│
├── docs/                                # Master HTML documentation, diagnostics & screenshots
│   ├── documentation.html               # Master comprehensive settings guide
│   ├── diagnose.html                    # Hardware & model telemetry dashboard
│   └── screenshots/                     # 2000% zoom & studio feature galleries
├── md/                                  # Centralized Markdown documentation hub
│   ├── README.md                        # Documentation index & reading guide
│   ├── CLAUDE.md                        # Complete developer manual & API reference
│   ├── BRAIN.md                         # Architectural memory & system design
│   ├── CHANGELOG.md                     # Version history & release notes
│   ├── CHAT_TRANSCRIPT.md               # Development audit trail & execution log
│   └── TODO.md                          # Roadmap & completed milestones
├── tests/                               # Test suites, benchmarks & verification scripts
├── scripts/                             # Model downloaders & automation scripts
└── samples/                             # Test assets (logos, sketches, photos)
```

---

## 💻 Installation & Setup

### Prerequisites
- **Operating System**: Windows 10 or 11 (64-bit)
- **Python**: 3.10+ (Tested & verified on Python 3.14.6 AMD64)
- **Node.js**: 18+ (Tested & verified on Node 24+)
- **Git**: Installed

---

### Step 1: Clone Repository
```powershell
git clone https://github.com/abidalidevv/Vectorize-your-image-Fix-and-Convert-Blurry.git
cd Vectorize-your-image-Fix-and-Convert-Blurry
```

---

### Step 2: Set Up Python Backend
```powershell
cd backend

# Create and activate virtual environment (optional but recommended)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

#### 🚀 Optional: Pre-Download All AI Models (1-Click / One-Time)
To use all Pro features (BiRefNet BG Remover, GFPGAN Face Restorer, Real-ESRGAN Upscaler, LaMa Magic Eraser) completely offline without live HTTP download delays:

- **Windows (1-Click)**:
  Simply double-click `download_models.bat` in the project root, or run in terminal:
  ```powershell
  .\download_models.bat
  ```

- **Linux / macOS**:
  ```bash
  chmod +x download_models.sh
  ./download_models.sh
  ```

The script automatically verifies existing caches and downloads any missing model weights:
- **GFPGAN v1.4 (~324.5MB)** & **YuNet (~0.2MB)**: Face & Eye Restoration
- **LaMa FP32 (~198.4MB)**: Magic Eraser Inpainting
- **BiRefNet Ultra (~972MB)** & **ISNet (~178.6MB)**: High-resolution Matting BG Remover
- **RealESRGAN_x4plus (~67.1MB)** & **Real-ESRGAN v3 (~4.9MB)**: AI Super-Resolution

*(You can also run the Python scripts directly: `python scripts/download_new_models.py` and `python scripts/download_pro_models.py`)*

Alternatively, you can pre-download them with one-line Python commands:
- **RealESRGAN_x4plus Ultra Model (~67MB)**:
  ```powershell
  python scripts/download_pro_models.py --realesrgan-plus
  ```
- **BiRefNet Ultra Model (~972MB)**:
  ```powershell
  python -c "from rembg import new_session; new_session('birefnet-general'); print('BiRefNet cached successfully!')"
  ```
- **Real-ESRGAN v3 Fast Model (~4.8MB)**:
  ```powershell
  python -c "import urllib.request, pathlib; p = pathlib.Path.home() / '.cache' / 'realesrgan' / 'realesr-general-x4v3.onnx'; p.parent.mkdir(parents=True, exist_ok=True); urllib.request.urlretrieve('https://huggingface.co/Heliosoph/realesrgan-onnx/resolve/main/realesr-general-x4v3.onnx', str(p)); print('Real-ESRGAN Fast cached!')"
  ```

*(Note: If uncached, the server automatically degrades gracefully to Fast mode—`isnet-general-use` for Background Removal and `realesr-general-x4v3` / `Lanczos-4` for Image Enhancer—without blocking live requests).*

---

### Step 3: Set Up Frontend
```powershell
cd ..\frontend

# Install npm dependencies
npm install
```

---

## 🏃 Running the Application

### 1. Start the Backend Server (Port 8000)
```powershell
cd backend\app
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```
- API Health: `http://127.0.0.1:8000/health`
- Interactive Swagger UI: `http://127.0.0.1:8000/docs`

### 2. Start the Frontend Dev Server (Port 5173)
```powershell
cd frontend
npm run dev
```
- Web Studio: `http://localhost:5173`

---

## 🧪 Testing & Verification

Vectorizer AI includes automated test suites covering all computer-vision pipelines, neural models, vectorization engines, and HTTP routes.

```powershell
# Run backend pytest suite (21/21 tests passing)
python -m pytest backend/tests/test_vectorforge.py -v

# Inspect live telemetry & model cache verification
curl http://127.0.0.1:8000/api/diagnostics

# Build frontend production bundle
cd frontend
npm run build
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Server health check & version info |
| `GET` | `/api/diagnostics` | Full system health, ONNX providers, hardware RAM, and 4-model cache verification |
| `POST` | `/api/upload` | Multipart upload (PNG, JPG, BMP, WebP) with dimension validation |
| `POST` | `/api/analyze` | Returns edge density, color variance, and recommended mode |
| `POST` | `/api/preprocess` | Applies denoise, contrast, sharpen, or bg-removal |
| `POST` | `/api/quantize` | Reduces color palette using K-Means or Median-Cut |
| `POST` | `/api/vectorize` | Executes VTracer / Contour tracing and returns SVG URL + stats |
| `POST` | `/api/remove-bg` | Studio AI background removal (`quality`: "fast" [isnet] \| "ultra" [birefnet], defringe choke, feather, color decontamination) |
| `POST` | `/api/enhance` | Studio AI super-resolution (`quality`: "fast" [x4v3] \| "ultra" [x4plus], scale, 6-stage classical enhancement) |
| `GET` | `/api/svg/{session_id}` | Serves the generated SVG file directly |
| `POST` | `/api/export/svg` | Exports optimized SVG with `scour` |
| `POST` | `/api/export/png` | Renders high-res raster PNG via `resvg` at 1×, 2×, 4×, 8× |
| `DELETE` | `/api/session/{session_id}` | Cleans up session temporary files |

---

## 🗺️ Roadmap & Future Enhancements

- [x] VTracer Rust curve fitting & Bezier spline tracing
- [x] Intelligent mode analysis & auto-recommendation
- [x] Split-view comparison slider with 2000% zoom
- [x] Mobile & tablet responsive workspace navigation
- [x] High-resolution multi-scale PNG export with `resvg-py`
- [x] **AI Background Removal Studio**: Dual-tier Fast (`isnet-general-use`) & Ultra Pro (`birefnet-general`)
- [x] **Edge Halo Choke & Physical Alpha-Unmixing Color Decontamination**: Mathematical edge fringe eradication
- [x] **AI Image Enhancer Studio**: Dual-tier Fast (`realesr-general-x4v3`) & Ultra Pro (`RealESRGAN_x4plus`) + 6-stage CV pipeline
- [x] **Live System & Model Diagnostics**: Interactive `diagnose.html` dashboard & `/api/diagnostics` telemetry
- [x] **Resumable Multi-Model Downloader**: CLI script with HTTP Range resumption (`download_pro_models.py`)
- [ ] **Batch Processing Mode**: Queue multiple images for bulk vectorization
- [ ] **Desktop App Packaging**: Standalone offline executable using Tauri or Electron
- [ ] **Direct EPS & PDF Vector Export**: Export directly to Adobe Illustrator EPS and print-ready PDF vectors
- [ ] **WebAssembly In-Browser Tracer**: Client-side WASM engine fallback for serverless hosting

---

## 👨‍💻 Author & Connect

**Abid Ali**  
Full-Stack Engineer & AI Developer  

- 🌐 **Portfolio Website**: [abidalidev.com](https://abidalidev.com)
- 🐙 **GitHub**: [@abidalidevv](https://github.com/abidalidevv)
- 📦 **Repository**: [Vectorize-your-image-Fix-and-Convert-Blurry](https://github.com/abidalidevv/Vectorize-your-image-Fix-and-Convert-Blurry)

---

## 📄 License

This project is licensed under the [MIT License](LICENSE) — free for personal and commercial use.
