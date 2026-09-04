# Changelog

All notable changes to **VectorForge AI** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
