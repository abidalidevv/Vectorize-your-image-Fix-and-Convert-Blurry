# 🤖 VectorForge AI — Antigravity Agent Guidelines (GEMINI.md)

> **Master Guide for Antigravity AI Pair Programmer**  
> **Repository**: [Vectorize-your-image-Fix-and-Convert-Blurry](https://github.com/abidalidevv/Vectorize-your-image-Fix-and-Convert-Blurry)  
> **Reference**: See [`AGENTS.md`](AGENTS.md) and [`md/BRAIN.md`](md/BRAIN.md) for full architectural memory.

---

## ⚡ Quick Context for Antigravity Resuming This Project

When working on VectorForge AI after weeks, months, or a year, here is everything you need to know immediately:

1. **Hierarchy Mode**: Always keep `hierarchical = "cutout"` in `backend/app/vectorization/vtracer_engine.py` and `engine_selector.py`. Never use `stacked` for color, as it creates giant dark background wedges and color bleed.
2. **Sub-Pixel Seams**: Cutout mode antialiasing seams are eliminated by injecting `<rect width="100%" height="100%" fill="{bg_color}"/>` behind opaque images.
3. **Outlines & Anti-Alias Filtering**: Connected components (`cv2.connectedComponentsWithStats`, `MAX_ANTIALIAS_COMPONENT_PX = 40`) preserve thin continuous borders (like the dark brown triangle border) while cleaning corner intersection noise.
4. **Offline AI Models**: Models are gitignored in `backend/app/weights/`. Run `download_models.bat` (Windows) to fetch all weights.
5. **Dev Servers**:
   - Backend: `cd backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`
   - Frontend: `cd frontend && npm run dev`
6. **Tests**: `pytest backend/tests/test_vectorforge.py -v` (23/23 passing).
7. **Complete History**: Read [`md/CHAT_TRANSCRIPT.md`](md/CHAT_TRANSCRIPT.md) for full conversation memory and previous debugging decisions. Update it with `python scripts/export_chat.py`.
