"""
VectorForge AI — Remove BG Studio Engine
High-quality background removal using AI Segmentation (rembg isnet-general-use) and high-speed
OpenCV GrabCut & Border-Seed FloodFill with edge feathering and defringing.
"""
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

# Cache rembg status & sessions
_REMBG_AVAILABLE = None
_REMBG_SESSION = None
_BIREFNET_SESSION = None
try:
    import rembg
    _REMBG_AVAILABLE = True
except Exception:
    _REMBG_AVAILABLE = False


def _get_rembg_session():
    """Get or lazily initialize the rembg session for Fast tier (isnet-general-use)."""
    global _REMBG_SESSION
    if _REMBG_SESSION is None:
        import rembg
        _REMBG_SESSION = rembg.new_session("isnet-general-use")
    return _REMBG_SESSION


def _is_birefnet_lite_cached() -> bool:
    """Check if the ~213MB birefnet-general-lite model is already downloaded locally."""
    candidates = [
        Path.home() / ".rembg" / "models" / "birefnet-general-lite" / "birefnet-general-lite.onnx",
        Path.home() / ".u2net" / "birefnet-general-lite.onnx",
    ]
    for p in candidates:
        if p.exists() and p.stat().st_size > 100_000_000:
            return True
    return False


def _is_birefnet_cached() -> bool:
    """Check if any BiRefNet model weights (Lite or General) are cached locally."""
    if _is_birefnet_lite_cached():
        return True
    candidates = [
        Path.home() / ".rembg" / "models" / "birefnet-general" / "birefnet-general.onnx",
        Path.home() / ".u2net" / "birefnet-general.onnx",
    ]
    for p in candidates:
        if p.exists() and p.stat().st_size > 100_000_000:
            return True

    if _REMBG_AVAILABLE:
        try:
            import rembg.sessions.birefnet_general
            resolved = rembg.sessions.birefnet_general.BiRefNetSessionGeneral.resolve_existing("birefnet-general.onnx")
            if resolved and Path(resolved).exists() and Path(resolved).stat().st_size > 100_000_000:
                return True
        except Exception:
            pass

    return False


def _get_birefnet_session():
    """Get or lazily initialize the rembg session for Ultra/Pro tier (BiRefNet Lite or General)."""
    global _BIREFNET_SESSION
    if _BIREFNET_SESSION is None:
        import rembg
        import onnxruntime as ort
        sess_opts = ort.SessionOptions()
        sess_opts.inter_op_num_threads = 2
        sess_opts.intra_op_num_threads = 4

        # 1. Prefer birefnet-general-lite on CPU for high performance and stability without memory arena crashes
        if _is_birefnet_lite_cached():
            try:
                logger.info("Initializing BiRefNet-general-lite session for Pro mode...")
                _BIREFNET_SESSION = rembg.new_session("birefnet-general-lite", sess_opts=sess_opts)
                return _BIREFNET_SESSION
            except Exception as e:
                logger.warning(f"Failed to init birefnet-general-lite with options: {e}. Trying default...")
                try:
                    _BIREFNET_SESSION = rembg.new_session("birefnet-general-lite")
                    return _BIREFNET_SESSION
                except Exception as e2:
                    logger.warning(f"Default birefnet-general-lite failed: {e2}")

        # 2. Fallback to birefnet-general if present
        try:
            logger.info("Initializing BiRefNet-general session...")
            _BIREFNET_SESSION = rembg.new_session("birefnet-general", sess_opts=sess_opts)
        except Exception as e:
            logger.warning(f"Failed to init birefnet-general with options: {e}")
            try:
                _BIREFNET_SESSION = rembg.new_session("birefnet-general")
            except Exception as e2:
                logger.error(f"BiRefNet session creation failed: {e2}")
                return None

    return _BIREFNET_SESSION


def _is_rembg_cached() -> bool:
    """Check if the ~170MB isnet-general-use model is already downloaded locally."""
    candidates = [
        Path.home() / ".u2net" / "isnet-general-use.onnx",
        Path.home() / ".rembg" / "models" / "isnet-general-use" / "isnet-general-use.onnx",
    ]
    for p in candidates:
        if p.exists() and p.stat().st_size > 10_000_000:
            return True

    if _REMBG_AVAILABLE:
        try:
            import rembg.sessions.dis_general_use
            resolved = rembg.sessions.dis_general_use.DisSession.resolve_existing("isnet-general-use.onnx")
            if resolved and Path(resolved).exists() and Path(resolved).stat().st_size > 10_000_000:
                return True
        except Exception:
            pass

    return False


def _remove_bg_rembg(img: Image.Image) -> Optional[Image.Image]:
    """Try to remove background using rembg Fast model (isnet-general-use) with memory protection."""
    if not _REMBG_AVAILABLE:
        return None
    try:
        import rembg
        session = _get_rembg_session()
        w, h = img.size
        max_dim = 800
        if max(w, h) > max_dim:
            scale = max_dim / max(w, h)
            small = img.resize((int(w * scale), int(h * scale)), Image.Resampling.BILINEAR)
            cutout_small = rembg.remove(small, session=session)
            alpha_small = cutout_small.split()[3]
            alpha_orig = alpha_small.resize((w, h), Image.Resampling.BILINEAR)
            cutout = img.convert("RGBA")
            cutout.putalpha(alpha_orig)
            return cutout
        else:
            return rembg.remove(img, session=session)
    except Exception as e:
        logger.warning(f"rembg Fast removal failed: {e}")
        return None


def _remove_bg_birefnet(img: Image.Image) -> Optional[Image.Image]:
    """Try to remove background using rembg Ultra model (birefnet-general) with memory protection."""
    if not _REMBG_AVAILABLE:
        return None
    try:
        import gc
        gc.collect()
        import rembg
        session = _get_birefnet_session()
        w, h = img.size
        max_dim = 1024
        if max(w, h) > max_dim:
            scale = max_dim / max(w, h)
            small = img.resize((int(w * scale), int(h * scale)), Image.Resampling.BILINEAR)
            cutout_small = rembg.remove(small, session=session)
            alpha_small = cutout_small.split()[3]
            alpha_orig = alpha_small.resize((w, h), Image.Resampling.BILINEAR)
            cutout = img.convert("RGBA")
            cutout.putalpha(alpha_orig)
            return cutout
        else:
            return rembg.remove(img, session=session)
    except Exception as e:
        logger.warning(f"BiRefNet Ultra removal failed: {e}")
        return None
    finally:
        try:
            import gc
            gc.collect()
        except Exception:
            pass


def _estimate_background_color(arr_rgb: np.ndarray) -> np.ndarray:
    """Sample outer borders to robustly determine average/median background color."""
    top = arr_rgb[0, :, :3]
    bottom = arr_rgb[-1, :, :3]
    left = arr_rgb[:, 0, :3]
    right = arr_rgb[:, -1, :3]
    border_pixels = np.vstack([top, bottom, left, right])
    return np.median(border_pixels, axis=0).astype(np.float32)


def _decontaminate_color(
    arr_rgba: np.ndarray,
    bg_color: Optional[np.ndarray] = None
) -> np.ndarray:
    """
    Color decontamination for semi-transparent edge pixels (0 < alpha < 255):
    true_fg_color = (observed_color - background_color * (1 - alpha/255)) / (alpha/255)
    Removes residual background halo bleeding at transparent edges.
    """
    if bg_color is None:
        bg_color = _estimate_background_color(arr_rgba)

    rgb = arr_rgba[:, :, :3].astype(np.float32)
    raw_alpha = arr_rgba[:, :, 3]
    alpha = raw_alpha.astype(np.float32) / 255.0

    # Only apply to semi-transparent fringe pixels (0 < alpha < 255)
    fringe_mask = (raw_alpha > 0) & (raw_alpha < 255)
    if not np.any(fringe_mask):
        return arr_rgba

    alpha_safe = np.maximum(alpha[..., np.newaxis], 1.0 / 255.0)
    bg_broadcast = bg_color.reshape((1, 1, 3))

    decontaminated = (rgb - bg_broadcast * (1.0 - alpha_safe)) / alpha_safe
    decontaminated = np.clip(decontaminated, 0.0, 255.0)

    result = arr_rgba.copy()
    result_rgb = result[:, :, :3]
    result_rgb[fringe_mask] = decontaminated[fringe_mask].astype(np.uint8)
    result[:, :, :3] = result_rgb
    return result


def _remove_bg_opencv(
    img: Image.Image,
    tolerance: float = 35.0,
    contiguous: bool = False,
) -> Image.Image:
    """
    High-precision local OpenCV background removal:
    1. Sample outer border pixels to robustly detect dominant background color.
    2. Compute Euclidean color distance to background in RGB color space.
    3. If contiguous=True: Seeded border floodfill (only removes background touching outer edge).
       If contiguous=False (default for drawings, text, logos, icons): Global color cutout
       (removes background everywhere, including inner loops).
    4. Anti-aliased soft alpha transition for clean, professional edges.
    5. Preserves existing alpha channels.
    """
    rgba = img.convert("RGBA")
    arr = np.array(rgba)
    h, w = arr.shape[:2]

    # Sample all 4 outer borders to robustly determine background color
    top = arr[0, :, :3]
    bottom = arr[-1, :, :3]
    left = arr[:, 0, :3]
    right = arr[:, -1, :3]
    border_pixels = np.vstack([top, bottom, left, right])
    bg_median = np.median(border_pixels, axis=0).astype(float)

    # Euclidean distance from background color
    diff = np.sqrt(np.sum((arr[:, :, :3].astype(float) - bg_median) ** 2, axis=2))

    if contiguous:
        # Only remove background connected to outer borders
        mask = (diff <= tolerance).astype(np.uint8) * 255
        fill_mask = np.zeros((h + 2, w + 2), dtype=np.uint8)
        step_x = max(1, w // 20)
        step_y = max(1, h // 20)
        for x in range(0, w, step_x):
            if mask[0, x] > 0 and fill_mask[1, x + 1] == 0:
                cv2.floodFill(mask, fill_mask, (x, 0), 255, loDiff=0, upDiff=0)
            if mask[h - 1, x] > 0 and fill_mask[h, x + 1] == 0:
                cv2.floodFill(mask, fill_mask, (x, h - 1), 255, loDiff=0, upDiff=0)
        for y in range(0, h, step_y):
            if mask[y, 0] > 0 and fill_mask[y + 1, 1] == 0:
                cv2.floodFill(mask, fill_mask, (0, y), 255, loDiff=0, upDiff=0)
            if mask[y, w - 1] > 0 and fill_mask[y + 1, w] == 0:
                cv2.floodFill(mask, fill_mask, (w - 1, y), 255, loDiff=0, upDiff=0)
        is_bg = (fill_mask[1:h + 1, 1:w + 1] > 0)
    else:
        # Global color removal (removes background everywhere)
        is_bg = (diff <= tolerance)

    # Antialiased soft alpha ramp for smooth cutout edges
    soft_ramp = 12.0
    alpha = np.clip((diff - tolerance) / max(1.0, soft_ramp) * 255, 0, 255).astype(np.uint8)
    if contiguous:
        alpha[~is_bg] = 255

    # If original image already had transparency, preserve it
    orig_alpha = arr[:, :, 3]
    alpha = np.minimum(alpha, orig_alpha)

    result = arr.copy()
    result[:, :, 3] = alpha
    return Image.fromarray(result, "RGBA")


def _refine_alpha(
    alpha: np.ndarray,
    feather_radius: float = 1.0,
    defringe_choke: int = 1
) -> np.ndarray:
    """
    Refine alpha mask:
    1. Defringe / Choke: Erode alpha mask by N pixels to remove colored boundary halos.
    2. Feather: Gaussian blur on alpha boundary for soft, organic edges.
    """
    refined = alpha.copy()

    # 1. Defringe / Choke
    if defringe_choke > 0:
        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE,
            (defringe_choke * 2 + 1, defringe_choke * 2 + 1)
        )
        refined = cv2.erode(refined, kernel)

    # 2. Feathering
    if feather_radius > 0.1:
        ksize = int(round(feather_radius * 4)) | 1
        refined = cv2.GaussianBlur(refined, (ksize, ksize), feather_radius)

    return refined


def _apply_background(
    fg_rgba: Image.Image,
    bg_type: str,
    bg_color: Optional[str]
) -> Image.Image:
    """
    Composite cutout over transparent, solid color, or gradient backdrop.
    """
    if bg_type == "transparent" or not bg_color or bg_color.lower() in ("transparent", "none"):
        return fg_rgba

    w, h = fg_rgba.size
    fg_arr = np.array(fg_rgba)
    alpha = (fg_arr[:, :, 3].astype(float) / 255.0)[:, :, np.newaxis]

    if bg_type == "gradient":
        hex_clean = bg_color.lstrip("#")
        r = int(hex_clean[0:2], 16)
        g = int(hex_clean[2:4], 16)
        b = int(hex_clean[4:6], 16)

        grad_top = np.array([min(255, int(r * 1.15)), min(255, int(g * 1.15)), min(255, int(b * 1.15))], dtype=float)
        grad_bottom = np.array([int(r * 0.75), int(g * 0.75), int(b * 0.75)], dtype=float)

        y_coords = np.linspace(0, 1, h)[:, np.newaxis, np.newaxis]
        bg_arr = grad_top * (1 - y_coords) + grad_bottom * y_coords
    else:
        # Solid color
        hex_clean = bg_color.lstrip("#")
        r = int(hex_clean[0:2], 16)
        g = int(hex_clean[2:4], 16)
        b = int(hex_clean[4:6], 16)
        bg_arr = np.full((h, w, 3), [r, g, b], dtype=float)

    # Alpha blending: out = fg * alpha + bg * (1 - alpha)
    composite = fg_arr[:, :, :3].astype(float) * alpha + bg_arr * (1.0 - alpha)
    composite = np.clip(composite, 0, 255).astype(np.uint8)

    out_rgba = np.dstack([composite, np.full((h, w), 255, dtype=np.uint8)])
    return Image.fromarray(out_rgba, "RGBA")


def remove_image_background(
    image_path: Path,
    params: Dict[str, Any],
    output_path: Path
) -> Tuple[List[str], int, int]:
    """
    Remove background from image with edge matting and optional replacement:
    - params.engine: 'auto' | 'ai' | 'color'
    - params.feather_radius: float (0.0 to 5.0)
    - params.defringe_choke: int (0 to 4)
    - params.bg_type: 'transparent' | 'color' | 'gradient'
    - params.bg_color: hex color code (e.g. '#ffffff' or '#0f172a')
    """
    changes: List[str] = []
    pil_img = Image.open(image_path)
    engine = params.get("engine", "auto")

    quality = str(params.get("quality", params.get("model_tier", "fast"))).lower()
    if quality in ("pro", "ultra"):
        quality = "ultra"
    else:
        quality = "fast"

    cutout_rgba: Optional[Image.Image] = None

    # ── Ultra Quality Mode (BiRefNet General) ──────────────────────────
    if quality == "ultra":
        if _is_birefnet_cached():
            logger.info("Using BiRefNet Ultra model for background removal...")
            cutout_rgba = _remove_bg_birefnet(pil_img)
            if cutout_rgba is not None:
                changes.append("AI Background Removal (BiRefNet Ultra)")
        else:
            logger.warning(
                "BiRefNet Ultra model weights not cached locally (~900MB). "
                "Falling back to Fast mode (isnet-general-use) to avoid live request delay."
            )

    # ── Fast Mode (isnet-general-use) ──────────────────────────────────
    if cutout_rgba is None:
        if _is_rembg_cached():
            logger.info("Using cached AI background removal (isnet-general-use)...")
            cutout_rgba = _remove_bg_rembg(pil_img)
            if cutout_rgba is not None:
                changes.append("AI Background Removal (isnet-general-use)")
        elif engine == "ai":
            logger.info("Attempting AI background removal (isnet-general-use)...")
            cutout_rgba = _remove_bg_rembg(pil_img)
            if cutout_rgba is not None:
                changes.append("AI Background Removal (isnet-general-use)")

    # ── Deterministic Fallback: OpenCV Cutout ──────────────────────────
    if cutout_rgba is None:
        logger.info("Using local OpenCV background removal...")
        tolerance = float(params.get("tolerance", 35.0))
        contiguous = bool(params.get("contiguous", False))
        cutout_rgba = _remove_bg_opencv(pil_img, tolerance=tolerance, contiguous=contiguous)
        mode_desc = "Border Cutout" if contiguous else "Full Color Cutout"
        changes.append(f"{mode_desc} (OpenCV)")

    # ── Refine Alpha Mask & Decontaminate Edge Colors ──────────────────
    feather_radius = float(params.get("feather_radius", 1.0))
    defringe_choke = int(params.get("defringe_choke", 1))

    arr = np.array(cutout_rgba)

    # 1. Defringe / Halo Choke: Erode alpha mask slightly inward (removes outermost fringe row)
    if defringe_choke > 0:
        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE,
            (defringe_choke * 2 + 1, defringe_choke * 2 + 1)
        )
        arr[:, :, 3] = cv2.erode(arr[:, :, 3], kernel)
        changes.append(f"Defringe halo choke ({defringe_choke}px)")

    # 2. Color Decontamination: Unmix background color from edge pixels (0 < alpha < 255)
    orig_rgba = np.array(pil_img.convert("RGBA"))
    bg_color_est = _estimate_background_color(orig_rgba)
    arr = _decontaminate_color(arr, bg_color=bg_color_est)

    # 3. Edge Feathering: Gaussian blur on alpha boundary for soft anti-aliased edge
    if feather_radius > 0.1:
        ksize = int(round(feather_radius * 4)) | 1
        arr[:, :, 3] = cv2.GaussianBlur(arr[:, :, 3], (ksize, ksize), feather_radius)
        changes.append(f"Edge feathering ({feather_radius:.1f}px)")

    cutout_rgba = Image.fromarray(arr, "RGBA")

    # ── Background Replacement ─────────────────────────────────────────
    bg_type = params.get("bg_type", "transparent")
    bg_color = params.get("bg_color", "transparent")

    final_img = _apply_background(cutout_rgba, bg_type=bg_type, bg_color=bg_color)
    if bg_type != "transparent" and bg_color not in ("transparent", "none"):
        changes.append(f"Replaced background with {bg_type} ({bg_color})")

    out_w, out_h = final_img.size
    output_path.parent.mkdir(parents=True, exist_ok=True)
    final_img.save(str(output_path), "PNG", optimize=True)

    logger.info(f"Background removed image saved to {output_path} ({out_w}x{out_h}), changes: {changes}")
    return changes, out_w, out_h


def remove_background(
    image_path: Path,
    output_path_or_params: Any = None,
    output_path: Optional[Path] = None,
) -> Tuple[List[str], int, int]:
    """
    Convenience wrapper for remove_image_background.
    Supports both:
      - remove_background(image_path, output_path)
      - remove_background(image_path, params, output_path)
    """
    if output_path is not None:
        if isinstance(output_path_or_params, dict):
            return remove_image_background(image_path, params=output_path_or_params, output_path=output_path)
        else:
            return remove_image_background(image_path, params={}, output_path=output_path)
    elif output_path_or_params is not None:
        if isinstance(output_path_or_params, (str, Path)):
            return remove_image_background(image_path, params={}, output_path=Path(output_path_or_params))
        elif isinstance(output_path_or_params, dict):
            default_out = image_path.parent / f"{image_path.stem}_cutout.png"
            return remove_image_background(image_path, params=output_path_or_params, output_path=default_out)
    default_out = image_path.parent / f"{image_path.stem}_cutout.png"
    return remove_image_background(image_path, params={}, output_path=default_out)


__all__ = ["remove_image_background", "remove_background"]
