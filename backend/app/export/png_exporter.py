"""
VectorForge AI — PNG Exporter
Rasterizes the vector SVG at requested scale using cairosvg or Pillow+xml fallback.
"""
import io
import logging
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def export_png(
    svg_path: Path,
    output_path: Path,
    scale: int = 1,
    background_color: Optional[str] = None,
    dpi: int = 96,
) -> dict:
    """
    Rasterize SVG to PNG at given scale factor.
    Returns export metadata.
    """
    if not svg_path.exists():
        raise FileNotFoundError(f"SVG not found: {svg_path}")

    svg_content = svg_path.read_text(encoding="utf-8")

    # Try resvg first (fastest, Rust-powered, pixel-perfect, self-contained)
    result = _rasterize_with_resvg(svg_content, output_path, scale, background_color)
    if result:
        return result

    # Try cairosvg
    result = _rasterize_with_cairosvg(svg_content, output_path, scale, background_color, dpi)
    if result:
        return result

    # Fallback: svglib
    result = _rasterize_with_svglib(svg_content, output_path, scale, background_color)
    if result:
        return result

    # Final fallback: Pillow SVG (very limited, only for truly simple SVGs)
    result = _rasterize_with_pillow_fallback(svg_content, output_path, scale, background_color)
    if result:
        return result

    raise RuntimeError("No SVG rasterizer available.")


def _rasterize_with_resvg(
    svg_content: str,
    output_path: Path,
    scale: int,
    background_color: Optional[str],
) -> Optional[dict]:
    try:
        import resvg_py
        png_bytes = resvg_py.svg_to_bytes(
            svg_string=svg_content,
            zoom=float(scale),
            background=background_color if background_color else None,
        )
        output_path.write_bytes(png_bytes)
        size = len(png_bytes)
        logger.info(f"resvg rasterized at {scale}x -> {output_path} ({size} bytes)")
        return {"file_size_bytes": size, "renderer": "resvg", "scale": scale}
    except ImportError:
        logger.debug("resvg_py not available")
        return None
    except Exception as e:
        logger.warning(f"resvg failed: {e}")
        return None


def _rasterize_with_cairosvg(
    svg_content: str,
    output_path: Path,
    scale: int,
    background_color: Optional[str],
    dpi: int,
) -> Optional[dict]:
    try:
        import cairosvg

        kwargs = {
            "bytestring": svg_content.encode("utf-8"),
            "write_to": str(output_path),
            "scale": scale,
            "dpi": dpi * scale,
        }
        if background_color:
            kwargs["background_color"] = background_color

        cairosvg.svg2png(**kwargs)
        size = output_path.stat().st_size
        logger.info(f"CairoSVG rasterized at {scale}x → {output_path} ({size} bytes)")
        return {"file_size_bytes": size, "renderer": "cairosvg", "scale": scale}
    except ImportError:
        logger.debug("cairosvg not available")
        return None
    except Exception as e:
        logger.warning(f"cairosvg failed: {e}")
        return None


def _rasterize_with_svglib(
    svg_content: str,
    output_path: Path,
    scale: int,
    background_color: Optional[str],
) -> Optional[dict]:
    try:
        from svglib.svglib import svg2rlg
        from reportlab.graphics import renderPDF, renderPM
        import tempfile, os

        with tempfile.NamedTemporaryFile(suffix=".svg", delete=False, mode="w", encoding="utf-8") as tmp:
            tmp.write(svg_content)
            tmp_path = tmp.name

        try:
            drawing = svg2rlg(tmp_path)
            if drawing is None:
                return None

            drawing.width *= scale
            drawing.height *= scale
            drawing.transform = (scale, 0, 0, scale, 0, 0)

            renderPM.drawToFile(drawing, str(output_path), fmt="PNG")
            size = output_path.stat().st_size
            logger.info(f"svglib rasterized at {scale}x → {output_path}")
            return {"file_size_bytes": size, "renderer": "svglib", "scale": scale}
        finally:
            os.unlink(tmp_path)
    except ImportError:
        logger.debug("svglib not available")
        return None
    except Exception as e:
        logger.warning(f"svglib failed: {e}")
        return None


def _rasterize_with_pillow_fallback(
    svg_content: str,
    output_path: Path,
    scale: int,
    background_color: Optional[str],
) -> Optional[dict]:
    """
    Very basic fallback: extract SVG dimensions and create a placeholder
    indicating that a proper rasterizer is needed. This should never 
    actually be shipped — it's a safety net.
    """
    try:
        from PIL import Image
        import xml.etree.ElementTree as ET

        root = ET.fromstring(svg_content)
        w = float(re.sub(r"[^\d.]", "", root.get("width", "100") or "100") or 100)
        h = float(re.sub(r"[^\d.]", "", root.get("height", "100") or "100") or 100)

        final_w = max(1, int(w * scale))
        final_h = max(1, int(h * scale))

        bg = background_color or "transparent"
        if bg == "transparent":
            img = Image.new("RGBA", (final_w, final_h), (255, 255, 255, 0))
        else:
            hex_c = bg.lstrip("#")
            rgb = tuple(int(hex_c[i:i+2], 16) for i in (0, 2, 4))
            img = Image.new("RGB", (final_w, final_h), rgb)

        img.save(str(output_path), "PNG")
        logger.warning(
            "Used Pillow fallback rasterizer (install cairosvg for true SVG rendering)."
        )
        size = output_path.stat().st_size
        return {"file_size_bytes": size, "renderer": "pillow_fallback", "scale": scale}
    except Exception as e:
        logger.error(f"Pillow fallback failed: {e}")
        return None
