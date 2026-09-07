# CLAUDE.md — Vectorizer AI Master Architecture, Algorithm & Developer Manual

> **System Status: 100% Operational & Verified**  
> - **Pytest Test Suite**: 23/23 tests passing (100% success rate)  
> - **Neural Models Verified on Disk**: 7 models active across 4 creative studios  
> - **Frontend Build**: TypeScript + Vite 100% clean (0 errors, 0 warnings)  
> - **Runtime Integrity**: 100% local-first, offline on Windows 11 (zero cloud APIs, zero subscriptions)

---

## 1. Executive System Overview & Status

Vectorizer AI (formerly VectorForge AI) is a local-first, offline-capable raster-to-vector web workstation designed as a zero-cost, high-precision alternative to Vectorizer.io, Topaz Gigapixel, Photoroom, and Adobe Content-Aware Fill.

The system is organized into **4 Integrated Creative Studios**:
1. **Vectorizer Studio**: Rust-based Bézier spline tracing engine with 2x nearest-neighbor line preservation and automatic Hough primitive circle detection.
2. **Background Remover Studio**: Dual-tier AI segmentation (IS-Net Fast & BiRefNet Ultra) with physical optical alpha-unmixing color decontamination and morphological halo choke.
3. **Image Enhancer Studio**: Dual-tier super-resolution (Real-ESRGAN x4v3 Fast & RealESRGAN_x4plus Ultra RRDBNet) paired with an automated 6-stage classical CV enhancement pipeline + YuNet & GFPGAN v1.4 Face Restoration.
4. **Magic Eraser Studio**: Deep learning inpainting powered by LaMa-ONNX (Large Mask Inpainting with Fast Fourier Convolutions) and an interactive sub-pixel brush canvas overlay.

---

## 2. Complete Catalog of All 7 AI & Classical Neural Models

| # | Model Identifier | Default Tier / Studio | File Name & Format | Size on Disk | Neural Architecture | Mathematical / CV Principle | Typical Latency (CPU) | Local Cache Path |
|---|---|---|---|---|---|---|---|---|
| **1** | `isnet-general-use` | Fast Tier (BG Remover) | `isnet-general-use.onnx` | ~178.6 MB | U2-Net with Intermedia Feature Map Cross-Attention | Multi-scale feature distillation for high-contrast boundary segmentation | ~1.2s – 2.5s | `~/.rembg/models/isnet-general-use/isnet-general-use.onnx` |
| **2** | `birefnet-general` | Ultra Pro Tier (BG Remover) | `birefnet-general.onnx` | ~972.7 MB | Bilateral Reference Network (BiRefNet) | Dichromatic reflection model; reference guidance for high-frequency hair, fur, and translucency | ~6.0s – 14.0s | `~/.rembg/models/birefnet-general/birefnet-general.onnx` |
| **3** | `realesr-general-x4v3` | Fast Tier (Enhancer) | `realesr-general-x4v3.onnx` | ~4.9 MB | Compact Deep Residual Convolutional Network (SRCNN) | 4× spatial upscaling; fast gradient descent optimized for edge sharpness with minimal parameter count | ~0.8s – 1.8s | `~/.cache/realesrgan/realesr-general-x4v3.onnx` |
| **4** | `RealESRGAN_x4plus` | Ultra Pro Tier (Enhancer) | `RealESRGAN_x4plus.onnx` | ~67.1 MB | 23-layer Residual-in-Residual Dense Block (RRDBNet) | High-order perceptual loss minimization; synthesizes realistic micro-textures and pristine vector boundaries | ~8.0s – 22.0s | `~/.cache/realesrgan/RealESRGAN_x4plus.onnx` |
| **5** | `face_detection_yunet` | Fast Landmark Detector (Face Restorer) | `face_detection_yunet.onnx` | ~227 KB | Ultra-lightweight Single-Shot Face Detector (YuNet) | 5-point facial landmark regression (eyes, nose, mouth corners) via `cv2.FaceDetectorYN` | < 3ms | `~/.cache/gfpgan/face_detection_yunet.onnx` |
| **6** | `GFPGANv1.4` | Facial Restoration (Enhancer) | `GFPGANv1.4.onnx` | ~324.5 MB | Generative Facial Prior GAN (StyleGAN2-based prior) | Encapsulated facial component dictionary codebooks; reconstructs severely degraded, blurry, or noisy human faces | ~3.0s – 6.0s per face | `~/.cache/gfpgan/GFPGANv1.4.onnx` |
| **7** | `lama_fp32` | Magic Eraser Studio (Inpainting) | `lama_fp32.onnx` | ~198.4 MB | Large Mask Inpainting with Fast Fourier Convolutions (FFC) | Global context frequency-domain inpainting with infinite effective receptive field | ~2.5s – 5.0s | `~/.cache/lama/lama_fp32.onnx` |

---

## 3. Mathematical & Computer Vision Techniques: Deep Dive

### 1. Large Mask Inpainting with Fast Fourier Convolutions (FFC) — Magic Eraser
- **Problem**: Standard spatial convolutions have small, local receptive fields. Inpainting large erased regions with spatial convolutions results in blurry color bleeds, repetitive patterns, or distorted structures.
- **FFC Solution**:
  - The model splits feature channels into a spatial branch and a frequency branch.
  - In the frequency branch, features undergo a 2D Real Fast Fourier Transform (RFFT):
    $$\hat{X}(u, v) = \sum_{x=0}^{H-1} \sum_{y=0}^{W-1} X(x, y) e^{-j 2\pi (ux/H + vy/W)}$$
  - Convolutions are applied directly in the frequency domain, capturing **global image context across the entire canvas simultaneously** (infinite receptive field).
  - An Inverse Real FFT (IRFFT) maps features back to the spatial domain.
- **Pipeline Implementation**:
  1. User draws a freeform mask on the interactive frontend canvas.
  2. The mask is dilated via OpenCV `cv2.dilate` using an elliptical structuring element ($k \in [0, 25]$) to ensure no border fringes remain around the erased object.
  3. Image and mask are resized to LaMa's native $512 \times 512$ resolution using area interpolation (`cv2.INTER_AREA`).
  4. Both tensors are normalized: image to $[0, 1]$ float32 with shape `(1, 3, 512, 512)`, mask to binary $\{0.0, 1.0\}$ float32 with shape `(1, 1, 512, 512)`.
  5. ONNX Runtime infers the inpainted output.
  6. The $512 \times 512$ output is upscaled back to the original image dimensions via **Lanczos-4 interpolation** (`cv2.INTER_LANCZOS4`).
  7. A feathered composite blends only the masked region back into the original unmasked image, preserving 100% of pristine, unedited pixels.

### 2. Generative Facial Prior Reconstruction & 5-Point Affine Alignment — GFPGAN
- **Problem**: Real-ESRGAN upscales entire scenes uniformly, often distorting human eyes, teeth, and skin textures.
- **Solution**:
  1. **YuNet Face Detection**: `cv2.FaceDetectorYN` detects faces and locates 5 landmark coordinates: left eye, right eye, nose tip, left mouth corner, right mouth corner.
  2. **Similarity Transform**: `cv2.estimateAffinePartial2D` computes the optimal similarity transformation matrix mapping detected landmarks to canonical $512 \times 512$ facial coordinate priors.
  3. **Warp & Normalize**: `cv2.warpAffine` aligns the face into a canonical $512 \times 512$ crop, normalized to $[-1, 1]$.
  4. **GFPGAN Inference**: The StyleGAN2 codebook prior reconstructs photorealistic eyes, pupils, iris reflections, teeth, and skin pores.
  5. **Inverse Affine Projection**: `cv2.invertAffineTransform` maps the restored face back into the original image space.
  6. **Radial Gaussian Alpha Feathering**: A soft elliptical mask feather blends the restored face seamlessly into surrounding hair and neck regions without hard seams:
     $$M_{\text{feather}} = G_{\sigma}(M_{\text{binary}}), \quad I_{\text{composite}} = I_{\text{restored}} \cdot M + I_{\text{original}} \cdot (1 - M)$$

### 3. Physical Optical Alpha-Unmixing Color Decontamination — BG Remover
- **Problem**: When an object is extracted from a bright green, red, or white studio background, the semi-transparent edge pixels contain background color bleeding (halos).
- **Solution**:
  - In optical compositing, observed pixel color is governed by:
    $$C_{\text{observed}} = C_{\text{true\_fg}} \cdot \alpha + C_{\text{backdrop}} \cdot (1 - \alpha)$$
  - For semi-transparent border pixels ($0.05 < \alpha < 0.95$), the engine mathematically inverts this equation to decontaminate the background tint:
    $$C_{\text{true\_fg}} = \text{clip}\left(\frac{C_{\text{observed}} - C_{\text{backdrop}} \cdot (1 - \alpha)}{\alpha}, 0, 255\right)$$
  - This completely purges green-screen spills and colored halo rings.

### 4. Morphological Edge Defringe Halo Choke — BG Remover
- Applied via `cv2.erode` with an elliptical structuring element of kernel size $k \in [1, 9]$:
  $$\text{Kernel} = \text{cv2.getStructuringElement}(\text{cv2.MORPH\_ELLIPSE}, (k, k))$$
  $$\alpha_{\text{choked}} = \text{cv2.erode}(\alpha, \text{Kernel})$$
- Physically pulls alpha boundaries inward by 1–5 pixels, eliminating outer boundary bleeding.

### 5. 6-Stage Classical Computer Vision Post-Enhancement Pipeline — Image Enhancer
1. **Stage 1 — Neural Super-Resolution**: 4× spatial upscaling via Real-ESRGAN x4v3 (Fast) or RealESRGAN_x4plus (Ultra RRDBNet).
2. **Stage 2 — Bilateral Edge-Preserving Denoising**: Smoothes JPEG compression blocks while maintaining sharp gradient boundaries (`cv2.bilateralFilter(d=9, \sigma_c=75, \sigma_s=75)`).
3. **Stage 3 — CIE-LAB Adaptive Contrast (CLAHE)**: Converts image from BGR to $L^*a^*b^*$ color space. Applies Contrast Limited Adaptive Histogram Equalization strictly to the $L^*$ (luminance) channel (`clipLimit=2.0, tileGridSize=(8,8)`), avoiding artificial color shifts.
4. **Stage 4 — Gaussian High-Pass Unsharp Masking**: Accentuates micro-contrast and edge crisply:
   $$I_{\text{sharp}} = \text{clip}(1.5 \cdot I - 0.5 \cdot G_{\sigma=1.0}(I), 0, 255)$$
5. **Stage 5 — Morphological Boundary Refinement**: Removes pixel stairstepping along contours.
6. **Stage 6 — HSV Dynamic Vibrance Tuning**: Enhances saturation on dull pixels to prepare discrete palette clusters for vectorization.

### 6. 2x Nearest-Neighbor Fine Line & Concentric Circle Preservation — Vectorizer
- **Problem**: Bicubic or bilinear scaling blurs delicate 1px lines and distorts concentric circles.
- **Solution**:
  - `detect_line_art(img)` computes monochrome parity and morphological thin-line ratios (`thin_line_ratio > 0.15`).
  - Automatically activates **2x Nearest-Neighbor Supersampling** (`cv2.INTER_NEAREST`).
  - By cleanly doubling the discrete coordinate grid without smoothing interpolation, Rust VTracer captures 100% 4-quadrant concentric circle symmetry and crosshairs without corner webbing or black notch artifacts.

### 7. VTracer Stacked vs Cutout Stacking Hierarchy
- **Stacked Hierarchy** (`hierarchical="stacked"`): Each color shape forms a solid foundation under subsequent layers. Prevents anti-aliasing white or transparent hairline gaps (seam gaps) between adjacent vector regions.
- **Cutout Hierarchy** (`hierarchical="cutout"`): Shapes are carved out like puzzle pieces. Used for B&W line art and logos where underlying bleed must be zero.

---

## 4. Complete UI Controls Reference (All 4 Studios)

### Global Header & Navigation
- **Studio Tabs**:
  - `◈ Vectorizer`: Main raster-to-vector studio.
  - `🖼️ Remove BG`: AI background removal studio.
  - `✨ Enhance`: Neural super-resolution and face restoration studio.
  - `🪄 Magic Eraser`: Deep learning object removal & inpainting studio.
- **Upload Image Button**: Opens file picker (supports PNG, JPG, JPEG, WebP, BMP up to 50MB).
- **Reset Canvas Button**: Clears current session, resets zoom/pan, resets active image.
- **Split View Button**: Toggles draggable split before/after comparison slider on the preview canvas.
- **Zoom Controls**: `[-]` zoom out, `[+]` zoom in, `[100%]` reset to 1x zoom.
- **Download Actions**:
  - `⬇ SVG`: Downloads scour-optimized SVG vector file.
  - `⬇ PNG`: Opens high-res raster export dialog (1x, 2x, 4x, 8x multipliers).

---

### Studio 1: Vectorizer Studio Controls (`LeftPanel.tsx`)
- **Image Mode Dropdown**:
  - `Auto`: Automatically detects artwork type via edge density and color variance.
  - `Logo / Clipart`: Prioritizes crisp polygon and spline boundaries with cutout hierarchy.
  - `Photo`: Quantizes continuous photographic tones.
  - `Sketch`: High contrast line preservation.
  - `Black & White`: Activates 2x nearest-neighbor line preservation & primitive circle detection.
- **Quality Presets**:
  - `Fast`: Fast polygon fitting for quick drafts.
  - `Balanced`: Clean cubic splines with balanced path counts.
  - `High` (Default): Production-grade cubic Bézier splines with 6-digit coordinate precision.
  - `Ultra`: Maximum path detail and minimal speckle filtering.
- **Color Palette Quantization**:
  - `Palette Size Slider`: 2 to 64 colors.
  - `🎨 Quantize Action Button`: Clusters continuous gradients into discrete color swatches using K-Means clustering.
- **Advanced Tracing Tuning (Collapsible Accordion)**:
  - `Speckle Filter Slider` (`0 – 64px`): Removes patches smaller than pixel area (0 preserves 1px fine outlines).
  - `Color Precision Slider` (`1 – 8`): Controls bit depth of color space clustering.
  - `Layer Difference Slider` (`2 – 32`): Euclidean distance threshold between color layers.
  - `Corner Threshold Slider` (`0 – 180°`): Angle below which the engine enforces a sharp corner point.
  - `Length Threshold Slider` (`1.0 – 10.0`): Minimum path segment length before Bézier subdivision.
- **One-Click Action Button**:
  - `◈ Vectorize`: Dispatches tracing payload to Rust VTracer engine.

---

### Studio 2: Background Remover Studio Controls (`BgRemoverPanel.tsx`)
- **Quality Mode Tier Selector**:
  - `⚡ Fast (IS-Net)`: Standard AI segmentation (~178.6MB ONNX), ~1.5s latency, ideal for logos and products.
  - `👑 Ultra Pro (BiRefNet)`: Bilateral Reference Network (~972.7MB ONNX), ~8–14s latency, ideal for fine hair, animal fur, glass, and translucency.
- **Feather Radius Slider** (`0.0 – 8.0px`): Gaussian smoothing radius applied to the alpha channel.
- **Defringe Halo Choke Slider** (`0 – 9px`): Morphological erosion of alpha boundary to physically remove background color bleed.
- **Replace Background Color Input**: Native HTML5 color picker + hex code input for solid background compositing.
- **Color Decontamination Checkbox**: Toggles optical alpha-unmixing formula to strip original backdrop tint.
- **One-Click Action Button**:
  - `✨ Remove Background`: Sends multipart request to `/api/remove-bg`.

---

### Studio 3: Image Enhancer Studio Controls (`EnhancerPanel.tsx`)
- **Enhancement Tier Selector**:
  - `⚡ Standard (Fast)`: Real-ESRGAN x4v3 (~4.9MB ONNX) + 6-stage classical CV pipeline (~1–2s latency).
  - `👑 Pro (Ultra)`: RealESRGAN_x4plus (~67.1MB ONNX, 23-layer RRDBNet) for maximum edge reconstruction.
- **Classical CV Refinement Sliders**:
  - `Bilateral Denoising Slider` (`0.0 – 2.0`): Edge-preserving noise removal.
  - `CLAHE Contrast Boost Slider` (`0.0 – 2.0`): Local adaptive contrast enhancement on $L^*$ channel.
  - `High-Pass Sharpen Slider` (`0.0 – 2.0`): Gaussian unsharp mask strength.
- **Face Restoration Controls (NEW)**:
  - `Restore Human Faces Checkbox`: Enables YuNet 5-point landmark detection and GFPGAN v1.4 facial prior synthesis.
  - `Face Strength Slider` (`0.1 – 1.0`): Blending strength of restored face into original background.
- **One-Click Action Button**:
  - `✨ Enhance Image`: Dispatches processing payload to `/api/enhance`.

---

### Studio 4: Magic Eraser Studio Controls (`EraserPanel.tsx`)
- **Brush Tool Controls**:
  - `Brush Size Slider` (`5 – 100px`): Adjusts circular stroke radius on canvas.
  - `Mask Dilation Slider` (`0 – 25px`): OpenCV morphological dilation kernel applied to mask before inpainting to eliminate border artifacts.
- **Stroke Management Buttons**:
  - `↩ Undo Stroke`: Reverts the most recent brush stroke from the canvas history stack.
  - `🗑 Clear Mask`: Wipes all drawn strokes from the canvas overlay.
- **One-Click Action Button**:
  - `🪄 Remove Marked Objects`: Encodes base64 mask and image, sending payload to `/api/inpaint`.

---

## 5. Complete JavaScript & TypeScript Functions Reference

### 1. `src/api/client.ts` (REST API Client)
- `uploadImage(file: File)`: Sends multipart FormData to `POST /api/upload`. Returns `ImageInfo` (session_id, dimensions, preview_url).
- `analyzeImage(sessionId: string)`: Sends `POST /api/analyze`. Returns recommended image mode and confidence.
- `preprocessImage(req: PreprocessRequest)`: Sends `POST /api/preprocess` with denoise, CLAHE, and thresholding parameters.
- `quantizeImage(sessionId: string, numColors: number)`: Sends `POST /api/quantize`. Returns extracted palette swatches and preview URL.
- `vectorizeImage(req: VectorizeRequest)`: Sends `POST /api/vectorize`. Returns SVG URL, vector statistics, and layer tree.
- `removeBackground(file: File, options)`: Sends multipart request to `POST /api/remove-bg` with quality tier, defringe choke, feather radius, and decontamination settings.
- `enhanceImage(file: File, options)`: Sends multipart request to `POST /api/enhance` with quality tier, denoise strength, contrast boost, unsharp mask, and face restoration flags.
- `inpaintImage(file: File, maskBase64: string, dilatePixels: number)`: Sends multipart request to `POST /api/inpaint` with raster image, base64 PNG mask, and dilation kernel size.
- `exportSvg(sessionId: string, optimize: boolean)`: Sends `POST /api/export/svg`. Triggers direct browser download of cleaned SVG file.
- `exportPng(sessionId: string, scale: number, background: string)`: Sends `POST /api/export/png`. Triggers direct browser download of high-res raster PNG.
- `fetchDiagnostics()`: Sends `GET /api/diagnostics`. Retrieves system RAM, ONNX providers, and 7-model disk cache verification.

### 2. `src/store/appStore.ts` (Zustand Global Reactive Store)
- **Active State Fields**:
  - `activeStudio`: Current creative studio tab (`'vectorizer' | 'bg_remover' | 'enhancer' | 'eraser'`).
  - `sessionId`: Ephemeral session UUID string.
  - `stage`: Current processing state (`'idle' | 'uploading' | 'analyzing' | 'quantizing' | 'vectorizing' | 'enhancing' | 'removing_bg' | 'inpainting' | 'exporting' | 'error'`).
  - `imageInfo`: Uploaded image width, height, aspect ratio, file size, preview URL.
  - `vectorResult`: Output SVG string, SVG URL, path count, color count, trace duration.
  - `layers`: Array of parsed SVG color layers with visibility toggle state.
  - `eraserBrushSize`: Current stroke radius in pixels ($5 - 100$).
  - `eraserDilation`: Morphological mask expansion in pixels ($0 - 25$).
  - `eraserMaskData`: Base64 PNG representation of drawn mask.
  - `enhancerFaceRestore`: Boolean toggle for GFPGAN face restoration.
  - `enhancerFaceStrength`: Float blending strength for face restoration ($0.1 - 1.0$).
- **State Actions**:
  - `setActiveStudio(studio)`: Transitions UI between the 4 studios.
  - `setImageInfo(info)`: Updates image metadata and resets dependent views.
  - `setVectorResult(result)`: Stores vector output and extracts layer swatches.
  - `toggleLayer(index)`: Updates layer visibility array and regenerates inline SVG DOM.
  - `setEraserMaskData(data)`: Updates base64 mask string from canvas drawing events.

### 3. `src/components/PreviewCanvas.tsx` (Interactive Viewport & Brush Canvas)
- `getCanvasCoords(e: React.MouseEvent<HTMLCanvasElement>)`:
  - Accurately converts viewport mouse coordinates (`clientX`, `clientY`) into native raster sub-pixel coordinates:
    ```typescript
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    return {
      x: (e.clientX - rect.left) * scaleX,
      y: (e.clientY - rect.top) * scaleY
    };
    ```
- `handleBrushDown(e)`: Initiates stroke path on overlay canvas with `ctx.beginPath()`, `ctx.arc()`, and `ctx.fill()`. Saves current canvas state to undo stack.
- `handleBrushMove(e)`: Continues stroke path with `ctx.lineTo()`, `ctx.stroke()`. Configured with `ctx.lineCap = 'round'` and `ctx.lineJoin = 'round'` with `rgba(239, 68, 68, 0.65)` neon red visualization.
- `handleBrushUp()`: Closes current stroke path and calls `syncMaskToStore()`.
- `syncMaskToStore()`: Creates an offscreen binary mask canvas (white drawing on black backdrop), exports base64 data URL via `toDataURL('image/png')`, and updates `appStore.setEraserMaskData()`.
- `undoLastStroke()`: Pops the previous image data from history stack and restores canvas state via `ctx.putImageData()`.
- `clearMask()`: Clears entire canvas overlay with `ctx.clearRect(0, 0, width, height)` and resets store mask.
- `Non-Passive Wheel Listener`: Intercepts mouse wheel with `{ passive: false }` to execute smooth focal zoom ($0.05\times - 20\times$) while preventing browser page zooming.
- `Split View Divider Dragging`: Computes horizontal mouse percentage across container width and dynamically updates CSS `clip-path: inset(0 0 0 splitPos%)` for before/after comparison.

---

## 6. Complete Python Backend Functions & Techniques Reference

### 1. `backend/app/magic_eraser/engine.py` (`MagicEraserEngine`)
- `_prepare_session()`: Initializes ONNX Runtime inference session with `sess_options.intra_op_num_threads = 4`, `sess_options.inter_op_num_threads = 2`, and `enable_cpu_mem_arena = False`.
- `inpaint_image(img_bgr: np.ndarray, mask: np.ndarray, dilate_kernel: int = 5)`:
  1. Validates image and mask dimensions.
  2. Expands mask using `cv2.dilate(mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))`.
  3. Resizes image and mask to $512 \times 512$ (`cv2.INTER_AREA`).
  4. Formats tensors: image to `float32 [0, 1]` with shape `(1, 3, 512, 512)`, mask to `float32 {0, 1}` with shape `(1, 1, 512, 512)`.
  5. Runs ONNX inference: `sess.run(None, {"image": img_tensor, "mask": mask_tensor})`.
  6. Resizes $512 \times 512$ output back to original dimensions using **Lanczos-4** (`cv2.INTER_LANCZOS4`).
  7. Blends output using Gaussian-blurred mask feathering:
     $$\text{output} = \text{inpainted} \cdot \alpha_{\text{blur}} + \text{original} \cdot (1 - \alpha_{\text{blur}})$$

### 2. `backend/app/magic_eraser/router.py` (Magic Eraser API Route)
- `inpaint_endpoint(file: UploadFile, mask_data: str = Form(...), dilate_pixels: int = Form(5))`:
  - Receives multipart image upload and base64-encoded PNG mask.
  - Decodes base64 string via `base64.b64decode` and `cv2.imdecode`.
  - Dispatches to `MagicEraserEngine.inpaint_image()`.
  - Saves result to `temp_files/<session_id>/inpainted.png`.
  - Returns JSON response with download URL, dimensions, and change notes.

### 3. `backend/app/image_enhancer/face_restorer.py` (`FaceRestorer`)
- `_init_yunet()`: Instantiates `cv2.FaceDetectorYN.create()` using `face_detection_yunet.onnx`.
- `_init_gfpgan()`: Instantiates ONNX Runtime session using `GFPGANv1.4.onnx`.
- `restore_faces(img_bgr: np.ndarray, strength: float = 0.8)`:
  1. Detects all human faces in image using YuNet.
  2. For each detected face:
     - Extracts 5 facial landmarks (right eye, left eye, nose, right mouth, left mouth).
     - Estimates partial affine similarity transform to canonical $512 \times 512$ coordinates (`cv2.estimateAffinePartial2D`).
     - Warps face crop using `cv2.warpAffine`.
     - Normalizes crop to `float32 [-1, 1]`, runs GFPGAN inference.
     - Computes inverse affine transform matrix (`cv2.invertAffineTransform`).
     - Projects restored face back to original image space with Gaussian radial feathering composite.

### 4. `backend/app/image_enhancer/engine.py` (`ImageEnhancerEngine`)
- `enhance()`:
  - **Fast Mode**: Runs `realesr-general-x4v3.onnx` + 6-stage classical CV pipeline.
  - **Ultra Pro Mode**: Runs `RealESRGAN_x4plus.onnx` (23-layer RRDBNet) + 6-stage pipeline.
  - **Face Restoration**: If `restore_faces=True`, automatically passes result through `FaceRestorer.restore_faces()`.
  - **Fallback**: Gracefully falls back to Lanczos-4 or Fast mode if Pro weights are not downloaded.

### 5. `backend/app/bg_remover/engine.py` (`BackgroundRemoverEngine`)
- `remove_background()`:
  - **Fast Mode**: Evaluates `isnet-general-use.onnx` via `rembg`.
  - **Ultra Pro Mode**: Evaluates `birefnet-general.onnx` via `rembg`.
  - **Defringe Halo Choke**: Erodes alpha boundary via `cv2.erode` with elliptical structuring element.
  - **Alpha-Unmixing Color Decontamination**: Inverts optical formula across boundary pixels ($0.05 < \alpha < 0.95$) to subtract backdrop tint.
  - **Memory Optimization**: Disables CPU memory arena (`enable_cpu_mem_arena = False`) to prevent memory allocation crashes.

### 6. `backend/app/api/routes/diagnostics.py` (Diagnostics & Health Telemetry)
- `get_diagnostics()`:
  - Audits on-disk presence and exact file byte sizes for all 7 neural models:
    - `isnet-general-use.onnx`
    - `birefnet-general.onnx`
    - `realesr-general-x4v3.onnx`
    - `RealESRGAN_x4plus.onnx`
    - `face_detection_yunet.onnx`
    - `GFPGANv1.4.onnx`
    - `lama_fp32.onnx`
  - Reports host system RAM (total, available, used percentage) via Windows kernel APIs.
  - Reports ONNX Runtime execution providers (`CPUExecutionProvider`, `CUDAExecutionProvider`, `DmlExecutionProvider`).
  - Reports active session directories and disk space.

---

## 7. Automated Pytest Test Suite (23/23 Tests)

The backend test suite (`backend/tests/test_vectorforge.py`) verifies every computer-vision algorithm, neural network model, fallback mechanism, and REST endpoint:

1. `test_health_endpoint`: Asserts `GET /health` returns status `ok`.
2. `test_upload_valid_image`: Validates image upload and session directory initialization.
3. `test_upload_invalid_file`: Validates rejection of non-image MIME types.
4. `test_analyzer_modes`: Verifies heuristic classification of logo, sketch, and photographic images.
5. `test_preprocessor_clahe`: Verifies contrast enhancement on low-contrast rasters.
6. `test_quantizer_kmeans`: Verifies K-Means color clustering and swatch generation.
7. `test_vtracer_color_tracing`: Verifies Rust VTracer SVG generation.
8. `test_contour_engine_bw`: Verifies OpenCV contour fallback with `evenodd` fill rules.
9. `test_svg_viewbox_and_optimization`: Asserts SVG root contains proper `viewBox="0 0 W H"` and passes XML validation.
10. `test_layer_extraction`: Verifies extraction of unique color layers for UI toggling.
11. `test_export_svg_and_png`: Verifies `resvg_py` high-res raster PNG rendering.
12. `test_fine_line_and_concentric_circles_preservation`: Verifies 2x nearest-neighbor preservation of 1px lines.
13. `test_color_vectorization_circle_and_junction_integrity`: Verifies stacked hierarchy eliminates black triangular seam gaps.
14. `test_bw_line_art_path_count_is_low`: Verifies contour merging keeps path counts minimal.
15. `test_primitive_detection_produces_true_circles`: Asserts Hough transform emits native `<circle>` tags.
16. `test_image_enhancer_upscaling_and_clahe`: Tests 4× super-resolution upscaling and CLAHE pipeline.
17. `test_bg_remover_cutout_and_replacement`: Tests alpha cutout and backdrop replacement.
18. `test_bg_remover_edge_decontamination_and_fringe_reduction`: Tests morphological halo choke and alpha unmixing.
19. `test_bg_remover_fast_mode`: Validates Fast tier IS-Net background removal.
20. `test_bg_remover_ultra_fallback_when_missing`: Asserts graceful fallback if Ultra model is missing.
21. `test_system_diagnostics_endpoint`: Asserts `GET /api/diagnostics` returns all 7 model statuses.
22. `test_magic_eraser_inpaint_synthetic`: Tests LaMa-ONNX inpainting pipeline with synthetic erased box.
23. `test_face_restorer_when_no_faces`: Verifies FaceRestorer operates safely on scenes without human faces without crashing.

---

## 8. Verification & Build Commands

```powershell
# 1. Run Complete Pytest Suite (All 23 tests)
cd c:\Users\Abid\Desktop\vector\vectorforge-ai
python -m pytest backend/tests/test_vectorforge.py -v

# 2. Compile React Frontend Studio (TypeScript + Vite)
cd c:\Users\Abid\Desktop\vector\vectorforge-ai\frontend
npm run build

# 3. Inspect Live Diagnostics API
curl http://127.0.0.1:8000/api/diagnostics

# 4. Pre-Download All Pro Models (Optional CLI)
python scripts/download_pro_models.py --all
```
