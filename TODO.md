# Vectorizer AI Roadmap & TODO

Future enhancements and planned features for subsequent versions of Vectorizer AI.

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
