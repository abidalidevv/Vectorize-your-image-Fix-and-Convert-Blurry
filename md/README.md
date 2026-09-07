# 📚 VectorForge AI — Master Documentation Hub

Welcome to the **VectorForge AI** documentation library. All project design documents, architectural blueprints, developer guides, changelogs, and historical transcripts have been consolidated into this `md/` directory for clean organization.

---

## 📑 Documentation Index

| Document | Description | Key Topics |
| :--- | :--- | :--- |
| [🧠 **BRAIN.md**](BRAIN.md) | **Architectural Memory & Design Decisions** | System state, neural pipelines, canvas pan/zoom, session lifecycle, model specifications |
| [📖 **CLAUDE.md**](CLAUDE.md) | **Comprehensive Developer & Architecture Guide** | Environment setup, dev server commands, REST API schemas, frontend tokens, debugging guide |
| [📝 **CHANGELOG.md**](CHANGELOG.md) | **Version History & Release Notes** | Full version breakdown from v1.0.0 baseline to v1.2.0 Pro Suite (all features & fixes) |
| [📋 **TODO.md**](TODO.md) | **Development Roadmap & Feature Tracking** | Completed modules, verified bug fixes, performance benchmarks, future milestones |
| [💬 **CHAT_TRANSCRIPT.md**](CHAT_TRANSCRIPT.md) | **Interactive Development Audit Trail** | Chronological record of prompts, subagents, code replacements, and system trajectories |
| [📌 **CLAUDE_INSTRUCTIONS.md**](CLAUDE_INSTRUCTIONS.md) | **Agent Behavioral Reference** | Context rules and conventions for AI assistants working in this repository |

---

## 🚀 Quick Navigation

### 1. Architectural Overview ([BRAIN.md](BRAIN.md))
- **Core Vectorizer Engine**: VTracer (Rust-accelerated binary) with spline curve fitting and OpenCV contour preprocessing.
- **Image Enhancer**: Real-ESRGAN v3 (Standard) & RealESRGAN x4+ (Pro) with CLAHE adaptive contrast and GFPGAN face restoration.
- **Background Remover**: ISNet General (Standard) & BiRefNet Matting (Pro) with alpha defringing and color decontamination.
- **Magic Eraser**: Large Mask Inpainting (LaMa FFC) with 512px native reflection padding and Smart Object Snap expansion.

### 2. Developer Commands ([CLAUDE.md](CLAUDE.md))
```powershell
# Run Backend API Server (FastAPI + Uvicorn)
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Run Frontend Dev Server (Vite + React)
cd frontend
npm run dev

# Run Automated Test Suite (Pytest 23/23 tests)
pytest backend/tests/test_vectorforge.py

# Build Production Frontend Bundle
cd frontend
npm run build
```

### 3. Interactive Web Dashboards
In addition to Markdown documentation, two full HTML dashboards are available in `docs/`:
- **[Master Technical & Settings Guide](../docs/documentation.html)**: Interactive visual breakdown of all 4 studio tools, parameters, and zoom benchmarks.
- **[Hardware & Model Diagnostics Dashboard](../docs/diagnose.html)**: Real-time telemetry monitoring CPU/RAM, ONNX Runtime providers, and model weight verification.
