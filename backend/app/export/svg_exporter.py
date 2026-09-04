"""
VectorForge AI — SVG Exporter
"""
import logging
from pathlib import Path

from utils.svg_optimizer import optimize_svg, validate_svg

logger = logging.getLogger(__name__)


def export_svg(svg_path: Path, output_path: Path, optimize: bool = True) -> dict:
    """
    Export (optionally optimize) SVG to output path.
    Returns export metadata.
    """
    if not svg_path.exists():
        raise FileNotFoundError(f"SVG not found: {svg_path}")

    svg_content = svg_path.read_text(encoding="utf-8")

    if optimize:
        svg_content = optimize_svg(svg_content)

    output_path.write_text(svg_content, encoding="utf-8")
    size = output_path.stat().st_size

    validation = validate_svg(svg_content)

    return {
        "file_size_bytes": size,
        "valid": validation["valid"],
        "stats": validation["stats"],
    }
