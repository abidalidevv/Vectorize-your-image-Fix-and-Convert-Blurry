"""
VectorForge AI — SVG Optimizer and Validator
"""
import re
import io
import logging
from pathlib import Path
from typing import Optional
from lxml import etree

logger = logging.getLogger(__name__)

SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"


def parse_svg(svg_content: str) -> Optional[etree._Element]:
    """Parse SVG string to lxml element tree. Returns None on failure."""
    try:
        parser = etree.XMLParser(remove_comments=True, recover=True)
        root = etree.fromstring(svg_content.encode("utf-8"), parser=parser)
        return root
    except Exception as e:
        logger.error(f"SVG parse error: {e}")
        return None


def ensure_viewbox(svg_content: str) -> str:
    """Ensure SVG root has a viewBox attribute matching width/height."""
    root = parse_svg(svg_content)
    if root is None or root.get("viewBox"):
        return svg_content
    w = root.get("width")
    h = root.get("height")
    if w and h:
        try:
            w_val = float(re.sub(r"[^\d.]", "", w))
            h_val = float(re.sub(r"[^\d.]", "", h))
            if w_val > 0 and h_val > 0:
                root.set("viewBox", f"0 0 {w_val:g} {h_val:g}")
                return etree.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")
        except Exception as e:
            logger.warning(f"ensure_viewbox failed: {e}")
    return svg_content


def validate_svg(svg_content: str) -> dict:
    """
    Validate an SVG string.
    Returns a dict with 'valid', 'errors', and 'stats' keys.
    """
    errors = []
    stats = {
        "path_count": 0,
        "group_count": 0,
        "color_count": 0,
        "file_size_bytes": len(svg_content.encode("utf-8")),
        "width": 0.0,
        "height": 0.0,
        "has_viewbox": False,
        "contains_raster": False,
    }

    root = parse_svg(svg_content)
    if root is None:
        return {"valid": False, "errors": ["SVG failed to parse"], "stats": stats}

    # Check for viewBox
    viewbox = root.get("viewBox")
    if viewbox:
        stats["has_viewbox"] = True
        try:
            parts = viewbox.split()
            if len(parts) == 4:
                stats["width"] = float(parts[2])
                stats["height"] = float(parts[3])
        except (ValueError, IndexError):
            pass

    # Width/height from attributes
    if not stats["width"]:
        w = root.get("width", "0")
        try:
            stats["width"] = float(re.sub(r"[^\d.]", "", w) or "0")
        except ValueError:
            pass
    if not stats["height"]:
        h = root.get("height", "0")
        try:
            stats["height"] = float(re.sub(r"[^\d.]", "", h) or "0")
        except ValueError:
            pass

    # Count elements
    ns = {"svg": SVG_NS}
    try:
        all_elements = root.iter()
        paths = 0
        groups = 0
        colors = set()
        has_image = False

        for el in all_elements:
            tag = etree.QName(el.tag).localname if "{" in el.tag else el.tag
            if tag in ("path", "polygon", "polyline", "rect", "circle", "ellipse"):
                paths += 1
                # Collect fill colors
                fill = el.get("fill")
                if fill and fill not in ("none", "transparent", "inherit"):
                    colors.add(fill)
                style = el.get("style", "")
                m = re.search(r"fill:\s*([^;]+)", style)
                if m:
                    colors.add(m.group(1).strip())
            elif tag == "g":
                groups += 1
            elif tag == "image":
                has_image = True

        stats["path_count"] = paths
        stats["group_count"] = groups
        stats["color_count"] = len(colors)
        stats["contains_raster"] = has_image

        if paths == 0:
            errors.append("SVG contains no path/shape elements")
        if has_image:
            errors.append("SVG contains embedded raster image element")

    except Exception as e:
        errors.append(f"Element counting error: {e}")

    valid = len(errors) == 0
    return {"valid": valid, "errors": errors, "stats": stats}


def optimize_svg(svg_content: str) -> str:
    """
    Optimize SVG using scour if available, with safe fallback.
    """
    try:
        import scour.scour as scour_lib
        options = scour_lib.generateDefaultOptions()
        options.enable_viewboxing = True
        options.strip_comments = True
        options.strip_ids = False  # keep for layer identification
        options.remove_metadata = True
        options.shorten_ids = False
        options.indent_type = "none"
        options.newlines = False
        options.strip_xml_prolog = False
        options.remove_descriptive_elements = True
        optimized = scour_lib.scourString(svg_content, options)
        return optimized
    except Exception as e:
        logger.warning(f"SVG optimization failed (using original): {e}")
        return svg_content


def extract_layers_from_svg(svg_content: str) -> list[dict]:
    """
    Extract color layer information from SVG groups or paths.
    Returns list of layer info dicts.
    """
    root = parse_svg(svg_content)
    if root is None:
        return []

    layers = []
    seen_colors = {}
    idx = 0

    for el in root.iter():
        tag = etree.QName(el.tag).localname if "{" in el.tag else el.tag
        if tag in ("path", "polygon", "polyline", "rect", "circle", "ellipse"):
            fill = el.get("fill", "")
            style = el.get("style", "")
            m = re.search(r"fill:\s*([^;]+)", style)
            if m:
                fill = m.group(1).strip()

            if fill and fill not in ("none", "transparent", "inherit", ""):
                norm_fill = fill.lower()
                if norm_fill not in seen_colors:
                    # Convert color to hex
                    hex_color = normalize_color_to_hex(norm_fill)
                    seen_colors[norm_fill] = {
                        "index": idx,
                        "color_hex": hex_color,
                        "color_rgb": hex_to_rgb(hex_color),
                        "path_count": 0,
                        "visible": True,
                        "label": f"Layer {idx + 1}",
                    }
                    idx += 1
                seen_colors[norm_fill]["path_count"] += 1

    return list(seen_colors.values())


def normalize_color_to_hex(color: str) -> str:
    """Convert various color formats to #rrggbb hex."""
    color = color.strip()
    if color.startswith("#"):
        if len(color) == 4:
            return "#" + "".join(c * 2 for c in color[1:])
        return color[:7]

    # rgb(r,g,b) format
    m = re.match(r"rgb\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)", color)
    if m:
        r, g, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return f"#{r:02x}{g:02x}{b:02x}"

    return "#000000"


def hex_to_rgb(hex_color: str) -> list[int]:
    """Convert #rrggbb to [r, g, b]."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    if len(hex_color) >= 6:
        try:
            return [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]
        except ValueError:
            pass
    return [0, 0, 0]
