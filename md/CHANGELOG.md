# Changelog

All notable changes to **VectorForge AI** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.2.1] - 2026-09-07

### Fixed
- **Primitive Detector Line Deduplication**: Fixed axis-specific line deduplication logic in `detect_primitives()` so horizontal lines with identical coordinates are correctly merged rather than splitting into double lines.
- **Continuous Border & Outline Preservation**: Replaced pure percentage-based color merging in `vtracer_engine.py` with `cv2.connectedComponentsWithStats` continuity checks. Legitimate thin outlines and borders (e.g. triangle stroke) with large continuous pixel length are preserved and never merged into adjacent fill clusters.
- **Planar Cutout Hierarchy Enforcement**: Enforced `hierarchical: "cutout"` across presets and `engine_selector.py`. Eliminates SVG layer overlap, outline erasure, and underlying solid ghost wedges.
- **Opaque Base Background Rect**: Automatically adds a canvas-fitting background rect for opaque images in cutout mode, eliminating sub-pixel antialiasing transparency gaps (`0 transparent seam holes`).

### Added
- **1-Click AI Models Downloader**: Added `download_models.bat` (Windows) and `download_models.sh` (Linux/macOS) in repository root to verify caches and download all required neural weights (GFPGAN, YuNet, LaMa, Real-ESRGAN, BiRefNet, ISNet) with one click.

---

## [1.2.0] - 2026-09-06

### Added
- **Magic Eraser & Inpainting Studio (LaMa-ONNX)**:
  - Added brand-new 4th Studio Tool (`🪄 Magic Eraser`) for removing unwanted objects, text, logos, and watermarks.
  - Integrated `LaMa-ONNX` (~198.4MB ONNX) with Fast Fourier Convolutions (FFC) operating at native 512×512 resolution with Lanczos-4 resolution recovery.
  - Interactive HTML5 canvas brush overlay with synchronized pan, zoom, and live circular brush cursor matching visual screen size.
  - Brush radius slider (5px–120px) with quick presets (15px, 30px, 50px, 80px) and live circular preview.
  - Morphological mask dilation slider (0–25px) to expand mask boundary and eliminate edge halos.
  - Pro Tier edge-gradient smoothing and seam bilateral filtering.
  - Multi-level undo stack and clear mask controls.
  - One-click workflow routing to Vectorizer and Image Enhancer studios.
  - Added `POST /api/inpaint` backend route and `InpaintParams` schema.

- **Old Photo & Face Restoration AI (GFPGAN v1.4)**:
  - Integrated `GFPGANv1.4` (~324.5MB ONNX) into Image Enhancer Studio.
  - Integrated `YuNet` face landmark detector (`face_detection_yunet.onnx`, ~227KB) executing in <3ms on CPU.
  - Automatic 5-point landmark similarity transformation to align 512×512 facial canonical geometry (eyes, nose, mouth).
  - High-order Generative Facial Prior GAN reconstruction with inverse affine matrix projection and Gaussian radial falloff blending.
  - User-facing Face Restoration toggle and Face Detail Blend (Fidelity) slider (0.1–1.0).
  - Integrated into `✨ Photo Restore` preset.

- **Diagnostics & Telemetry Expansion**:
  - Expanded `GET /api/diagnostics` and `diagnose.html` to audit all 7 studio models.
  - Added dedicated status cards for GFPGAN, YuNet, and LaMa.

- **Automated Test Suite Expansion**:
  - Expanded unit test coverage to **23/23 passing tests** with zero failures (`test_magic_eraser_inpaint_synthetic`, `test_face_restorer_when_no_faces`, and updated diagnostics telemetry).

---

## [1.1.0] - 2026-09-06

### Added
- **Pro-Tier AI Background Removal Studio**:
  - **Fast Tier**: Upgraded default segmentation to `isnet-general-use` (~178.6MB ONNX), delivering high-precision boundary detection for graphic logos, app icons, and product cutouts (~1.5s–3.0s CPU).
  - **Ultra Pro Tier**: Integrated `birefnet-general` (~972.7MB ONNX), Bilateral Reference Network for state-of-the-art dichromatic matting (fine hair, animal fur, transparent glass, mesh fabrics).
  - **Morphological Halo Choke**: Added elliptical kernel erosion via `cv2.erode(mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))` ($k \in [1, 9]$) to pull alpha boundaries inward and physically strip background bleeding.
  - **Physical Alpha-Unmixing Color Decontamination**: Inverts optical composite blending to restore uncorrupted foreground RGB in boundary pixels ($0.05 < \alpha < 0.95$):
    $$\text{true\_fg} = \text{np.clip}\left(\frac{\text{observed} - \text{bg\_color} \cdot (1 - \alpha)}{\alpha}, 0, 255\right)$$
  - **Zero-Arena Memory Management**: Configured ONNX Runtime sessions with `enable_cpu_mem_arena = False`, `inter_op_num_threads = 2`, `intra_op_num_threads = 4`, and proactive `gc.collect()`, preventing Windows `BFCArena` 822MB memory allocation crashes.
  - **Resilient Fallback**: Automatic non-blocking fallback to Fast mode if `birefnet-general.onnx` is not cached locally.

- **Pro-Tier AI Image Enhancer Studio**:
  - **Fast Tier**: Configured `realesr-general-x4v3` (~4.9MB ONNX) as the new default AI super-resolution upscaler (~1–2s latency).
  - **Ultra Pro Tier**: Integrated `RealESRGAN_x4plus` (~67.1MB ONNX, 23-layer RRDBNet architecture) for maximum vector-ready perceptual super-resolution and fine contour synthesis.
  - **6-Stage Classical Enhancement Pipeline**:
    1. Neural Super-Resolution (x4v3 Fast or x4plus Ultra)
    2. Bilateral Filter (edge-preserving denoising)
    3. CIE-LAB CLAHE (contrast equalization on $L^*$ channel)
    4. Gaussian High-Pass Unsharp Masking ($I_{\text{sharp}} = 1.5 \cdot I - 0.5 \cdot G_\sigma(I)$)
    5. Morphological Edge Refinement (smoothes boundary stairstepping)
    6. HSV Dynamic Range & Saturation Vibrance Tuning
  - **Resilient Fallback**: Automatic non-blocking fallback to Fast mode or high-order Lanczos-4 if Ultra weights are uncached.

- **Interactive System & Model Diagnostics Tool (`diagnose.html` & `/api/diagnostics`)**:
  - Created standalone dark-mode diagnostics dashboard (`diagnose.html`) at root, `docs/`, and `frontend/public/`.
  - Added `GET /api/diagnostics` endpoint providing runtime telemetry: OS, CPU cores, RAM utilization, ONNX Runtime execution providers (`CPUExecutionProvider`, `CUDAExecutionProvider`, `DmlExecutionProvider`), and on-disk verification for all 4 neural models.
  - In-browser synthetic probe runner testing `/health`, `/api/diagnostics`, `/api/remove-bg`, and `/api/enhance` with live latency benchmarking.
  - One-click copyable JSON diagnostic report for troubleshooting.

- **Resumable Multi-Model Downloader (`scripts/download_pro_models.py`)**:
  - Chunked multi-threaded streaming downloader with HTTP Range header resume support, retry logic, and cache validation (`--all`, `--birefnet`, `--realesrgan-plus`, `--realesrgan`, `--isnet`).

- **Test Suite Expansion**:
  - Expanded unit test coverage from 11 to **21/21 passing tests** (`test_vectorforge.py`), verifying both AI models, fallbacks, color decontamination, defringe choke, and diagnostics telemetry.

---

## [1.0.6] - 2026-09-05

### Added
- **Split View Floating Indicators**:
  - Added floating status badges (`Original` on top-left and `Vector Output` on top-right) inside `PreviewCanvas` to clearly distinguish between the input raster and vectorized output.
  - Refined toolbar tab active states to seamlessly toggle off when Split mode is active.
- **Master Developer & Audit Documentation (`CLAUDE.md`)**:
  - Comprehensive rewrite of `CLAUDE.md` providing complete subsystem breakdowns, continuous-tone vs flat vector categorization, quantization recommendations for photographic posters, and full verification steps for future Claude audits.

---

## [1.0.5] - 2026-09-04

### Fixed
- **Concentric Circles & Fine Line Vectorization Restoration**:
  - **Severed Circle & Black Wedge Root Cause**: In v1.0.4, attempting to prevent intersection flaring via morphological subtraction (`thin_lines = bin_inv & ~thick_lines`) severed thin circles at crosshair intersections into disjoint arcs. Dilating those disconnected arcs produced bulbous endpoints, causing VTracer to invert quadrant polygons into massive solid black wedges and drop circular segments entirely.
  - **2× Clean Supersampling Pipeline**: Replaced all morphological erosion and dilation with **2× nearest-neighbor supersampling** in `line_detector.py`. Fine 1px lines cleanly scale to 2px in coordinate space with zero pinching, zero line severance, and zero corner webbing.
  - **Binary Cutout Tracing**: Traced in `trace_bw` with `colormode="binary"`, `hierarchical="cutout"`, `mode="spline"`, `filter_speckle=0`, `length_threshold=2.0`.
  - **Sub-Pixel ViewBox Scaling**: The SVG root preserves native 1× image dimensions with sub-pixel resolution via `width="{orig_w}" height="{orig_h}" viewBox="0 0 {orig_w*2} {orig_h*2}"`. Injects an opaque white `<rect>` for non-transparent drawings.
  - **Quadratic Symmetry & Verification Test**: Enhanced `test_fine_line_and_concentric_circles_preservation` in `backend/tests/test_vectorforge.py` with 4-quadrant symmetry verification, confirming identical dark-pixel distribution across all quadrants with 0 missing arcs.

---

## [1.0.4] - 2026-09-04

### Fixed
- **Circle Notch & Black Wedge Seam Gaps**: Fixed black triangular wedges at line intersections and stepped perimeter notches on circles.
  - **Stacked Hierarchy for Color Mode**: Restored `hierarchical="stacked"` across color presets (`fast`, `balanced`, `high`, `ultra`). This eliminated 1,632 transparent seam gap pixels where the dark studio canvas background was bleeding through acute corners as black triangular wedges.
  - **Continuous Circle Geometry**: In stacked mode, circle rims are vectorized as continuous, unbroken annular paths instead of being split into fragmented pieces, restoring perfectly smooth circular curvature with zero notches or dents.
  - **Optimal Default Preset Calibration**: Tuned default vectorization parameters (`qualityPreset: 'high'`, `colorPrecision: 7`, `layerDifference: 12`, `filterSpeckle: 1`, `lengthThreshold: 2.0`) so clicking "Vectorize" directly without changing settings immediately yields pristine, clean vectors.
  - **Automated Verification Test**: Added `test_color_vectorization_circle_and_junction_integrity` to verify 0 seam gap pixels, smooth circle circularity, and clean crossing junctions.

---

## [1.0.3] - 2026-09-04

### Added
- **Export & Download Modal**: Added a dedicated `ExportModal` component with SVG vector downloads, raw SVG markup clipboard copying, and high-resolution PNG rendering (1×, 2×, 4×, 8× / 300+ DPI).
- **Prominent Export Actions**: Placed a glowing `⤓ Export As…` button in the TopBar and an "Export Ready" quick-action card in the LeftPanel directly underneath the Vectorize button so downloads are always immediately accessible.
- **Professional Rebranding**: Rebranded product identity from VectorForge AI to **Vectorizer AI** across UI headers, logo badges, page titles, and metadata.

### Fixed
- **Line Junction Bulging & Trumpet Flares**: Eliminated junction filleting/webbing where concentric circles intersect crosshairs. Replaced morphological dilation with 2× bicubic supersampling and inverse SVG group scaling (`<g transform="scale(0.5)">`), guaranteeing clean, crisp, perpendicular intersections with zero line thickening.
- **Canvas Zoom Page Escalation**: Fixed mouse wheel zooming scaling the entire browser window instead of just the canvas. Replaced React passive synthetic events with native `{ passive: false }` wheel listeners, added `touch-action: none`, and blocked global `Ctrl+Wheel` page zoom. Zooming up to 2000% now smoothly focal-zooms the image while keeping all panels and navigation perfectly locked.
- **Optimal Default Preset Settings**: Switched default vectorization settings to High fidelity (`filterSpeckle: 0`, `colorPrecision: 7`, `lengthThreshold: 2.0`, `minArea: 1.0`) ensuring razor-sharp vector tracing out-of-the-box without requiring manual knob tweaking.

---

## [1.0.2] - 2026-09-04

### Fixed
- **Fine Line & Concentric Circle Preservation**: Fixed an issue where fine 1-pixel circular lines, radar rings, and technical line art were omitted in the vector output.
  - **Speckle & Hierarchy Root Cause**: In VTracer's default stacked mode, `filter_speckle=4` treated thin lines as noise, and stacked background polygons occluded thin foreground strokes.
  - **Line Art Detector (`line_detector.py`)**: Added automatic detection for fine line art and thin features (`thin_line_ratio > 0.15`).
  - **Fine Line Enhancement**: Applied sub-pixel orthogonal line reinforcement (`cv2.MORPH_CROSS`) so delicate 1-2px curves attain stable 2D manifolds during vectorization.
  - **Cutout Hierarchy & Zero-Speckle Tracing**: Forced `hierarchical="cutout"` and `filter_speckle=0` for line art and B&W modes, ensuring 100% of fine concentric circles and crosshairs are cleanly carved out and preserved.
  - **ContourEngine Compound Paths**: Fixed `ContourEngine` to use `cv2.RETR_CCOMP` with compound SVG paths (`fill-rule="evenodd"`), preventing nested concentric shapes from filling in as solid black disks.
- **Auto-mode Routing**: Updated `engine_selector.py` to automatically detect monochrome line art in `auto` mode and route to the high-fidelity line-preservation engine.
- **Comprehensive Unit Tests**: Added `test_fine_line_and_concentric_circles_preservation` verifying all 4 concentric rings (radii ~24, ~50, ~74, ~100) and the outer circle are intact.

---

## [1.0.1] - 2026-09-04

### Fixed
- **Tooltip Viewport Clipping**: Fixed hover hint tooltips in TopBar disappearing above the top of the browser viewport. Re-engineered tooltip positioning with `.topbar [data-tooltip]::after` and `[data-tooltip-pos="bottom"]` to open downward inside the visible viewport, with `[data-tooltip-align="right"]` to prevent horizontal clipping.
- **Mobile & Tablet Responsiveness**: Fixed 3-column desktop layout crushing the vector preview canvas on narrow viewports (<= 820px). Introduced a sleek segmented mobile workspace switch (`🎛 Controls`, `👁 Canvas`, `🎨 Layers`), giving each view 100% width and clean scrolling on tablet/mobile devices.
- **Compact Viewport Optimization**: Added responsive breakpoints for `<= 1080px`, `<= 820px`, `<= 640px`, and `<= 460px` adjusting TopBar button spacing, logo text, scale multipliers, and StatusBar items.

---

## [1.0.0] - 2026-09-04

### Added
- **Core Vectorization Engine**:
  - Rust-powered `VTracerEngine` for high-quality color Bézier curve tracing.
  - OpenCV `ContourEngine` fallback for monochrome and sketch tracing.
  - Automatic `engine_selector` that routes requests based on image properties.
- **Intelligent Pre-Analysis**:
  - Edge density detection using Sobel operators.
  - Color variance, saturation analysis, and unique color zone counting.
  - Automatic mode recommendation (`Logo`, `Illustration`, `Sketch`, `B&W`, `Photo`).
- **Color Quantization Pipeline**:
  - K-Means and Median-Cut algorithms for 2 to 64 color reduction.
  - Automated palette extraction with HEX, RGB, and coverage percentage stats.
- **Image Preprocessing**:
  - Bilateral and Gaussian noise reduction filters.
  - CLAHE contrast enhancement and unsharp mask sharpening.
  - Connected-component background removal with tolerance slider.
- **Export System**:
  - Scalable vector SVG export with `scour` optimizer and guaranteed `viewBox` insertion.
  - High-resolution PNG export powered by `resvg-py` (1x, 2x, 4x, 8x scale options).
- **Interactive Web Studio**:
  - Sleek dark-mode glassmorphism interface built with React 19 and Vite.
  - Zoom up to **2000%** with smooth drag-panning and mouse wheel zoom.
  - Split-slider comparison (raster original on left, vector output on right).
  - Palette inspector and SVG path/group statistics panel.
  - Drag-and-drop file upload and clipboard paste support (`PNG`, `JPG`, `BMP`, `WebP`).
- **Developer Guide & Test Suites**:
  - `CLAUDE.md` and `docs/CLAUDE_INSTRUCTIONS.md` with complete architectural documentation.
  - Pytest suite covering analyzer, quantizer, preprocessor, vtracer, contour engine, and exporters.
  - Python end-to-end API HTTP test suite (`tests/test_api_e2e.py`).

### Fixed
- Fixed `vtracer` PyO3 keyword argument parsing panic on Windows by utilizing strict positional parameters.
- Replaced Cairo/GTK requirement on Windows with self-contained `resvg-py` for clean PNG rasterization.
- Fixed lxml unicode serialization error in `ensure_viewbox` by enforcing UTF-8 encoding.
- Configured Vite reverse proxy to use IPv4 `127.0.0.1:8000` to prevent Node IPv6 connection errors.
