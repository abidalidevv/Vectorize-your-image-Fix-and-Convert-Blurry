# CLAUDE_INSTRUCTIONS.md — VectorForge AI Developer Guide

See [CLAUDE.md](../../CLAUDE.md) in the root directory for the complete guide.

## Summary Checklist for Claude:
1. **Always use positional arguments** when calling `vtracer.convert_image_to_svg_py`.
2. **Always call `ensure_viewbox(svg_content)`** on output SVGs to preserve responsive scaling and prevent clipping.
3. **Use `resvg_py`** for PNG rasterization at high resolution.
4. **Backend**: Run from `backend/app` with `python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload`.
5. **Frontend**: Run from `frontend` with `npm run dev`.
6. **Tests**: Run with `python -m pytest backend/tests/test_vectorforge.py -v` and `python tests/test_api_e2e.py`.
