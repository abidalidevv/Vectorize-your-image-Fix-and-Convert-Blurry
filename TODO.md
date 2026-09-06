# Vectorizer AI Roadmap & TODO

Future enhancements and planned features for subsequent versions of Vectorizer AI.

---

## Completed in v1.1.0 (Pro Tier)
- [x] **AI Background Remover Studio**:
  - [x] Fast Tier segmentation model (`isnet-general-use`, ~178.6MB ONNX).
  - [x] Ultra Pro Tier matting model (`birefnet-general`, ~972.7MB ONNX).
  - [x] Morphological Halo Choke (`cv2.erode` with elliptical structuring element).
  - [x] Physical Alpha-Unmixing Color Decontamination [$\text{true\_fg} = (\text{obs} - \text{bg}\cdot(1-\alpha))/\alpha$].
  - [x] Zero-Arena memory allocation optimization on CPU to prevent Windows 822MB crashes.
  - [x] Resilient non-blocking fallback to Fast mode if BiRefNet uncached.
- [x] **AI Image Enhancer Studio**:
  - [x] Fast Tier neural super-resolution (`realesr-general-x4v3`, ~4.9MB ONNX).
  - [x] Ultra Pro Tier deep super-resolution (`RealESRGAN_x4plus`, ~67.1MB ONNX, 23-layer RRDBNet).
  - [x] 6-Stage Classical Post-Enhancement Pipeline (Bilateral, CIE-LAB CLAHE, Gaussian Unsharp, Morphological Edge, HSV Vibrance).
  - [x] Resilient non-blocking fallback to Fast/Lanczos-4.
- [x] **Old Photo & Face Restoration AI (GFPGAN v1.4)**:
  - [x] High-precision YuNet 5-point facial landmark detector (<3ms CPU inference).
  - [x] 512×512 affine similarity alignment to center facial geometry and eye pupils.
  - [x] Generative Facial Prior GAN neural reconstruction for blurred, low-res, and scratched faces.
  - [x] Gaussian radial falloff blending and inverse affine projection preserves original composition.
  - [x] User-facing Fidelity slider (0.1–1.0) and toggle in Image Enhancer Studio.
  - [x] Auto-enabled when using `✨ Photo Restore` preset.
- [x] **Magic Eraser & Inpainting Studio (LaMa-ONNX)**:
  - [x] 4th Studio Tool with dedicated navigation tab and responsive controls.
  - [x] Large Mask Inpainting model with Fast Fourier Convolutions (FFC, ~198.4MB ONNX).
  - [x] Interactive HTML5 canvas brush overlay with synchronized zoom, pan, and real-time circular cursor.
  - [x] Configurable brush radius (5px–120px) with quick presets and live preview.
  - [x] Morphological mask dilation to expand brush margins and eliminate edge halos.
  - [x] Multi-level stroke undo stack and mask clearing.
  - [x] Seamless handoff from inpainting directly to Vectorizer and Image Enhancer.
- [x] **Interactive System Diagnostics & Telemetry**:
  - [x] Created `diagnose.html` interactive dashboard (dark glassmorphic UI).
  - [x] Auditing all 7 neural models (ISNet, BiRefNet, Real-ESRGAN Fast, RealESRGAN Ultra, GFPGAN, YuNet, LaMa).
  - [x] Added `GET /api/diagnostics` endpoint for live hardware, RAM load, and model verification.
  - [x] In-browser synthetic probe runner testing `/health`, `/api/diagnostics`, `/api/remove-bg`, and `/api/enhance`.
- [x] **Automated Test Suite Expansion**:
  - [x] 23/23 unit tests passing (`backend/tests/test_vectorforge.py`) including inpainting and face restoration test cases.

---

## Phase 2: Enhanced Editing & Vector Tweaking
- [ ] **Interactive Node / Path Editor**:
  - Ability to select individual SVG paths in the canvas.
  - Delete unwanted stray paths or dust artifacts.
  - Re-order layers (bring to front, send to back).
- [ ] **Color Replacement & Recolor Tool**:
  - Click on any color in the palette to change its hex value and update all matching SVG paths in real-time.
  - Merge adjacent colors with similar tones.
- [ ] **Gradient Mesh Support**:
  - Support linear and radial gradients during vectorization for photographic artwork.

---

## Phase 3: Export Formats & Batch Processing
- [ ] **Multi-Format Vector Export**:
  - Export to Adobe Illustrator compatible `.ai` or `.eps`.
  - Direct `.pdf` vector export with customizable DPI.
  - `.dxf` export for CNC and vinyl cutting machines.
- [ ] **Batch Processing Queue**:
  - Drag and drop a folder of images to process sequentially with saved presets.
  - Export all results into a `.zip` archive.

---

## Phase 4: Desktop Packaging
- [ ] **Standalone Windows Executable**:
  - Package FastAPI backend with PyInstaller.
  - Package frontend using Electron or Tauri for a 1-click desktop `.exe` installer.
  - System tray icon and native Windows notification when vectorization completes.
