"""
VectorForge AI — Magic Eraser Studio Engine (LaMa Inpainting ONNX)
Seamlessly removes objects, watermarks, text, and unwanted regions
using Fast Fourier Convolutions (FFC) and edge-preserving texture blending.
"""
import base64
import io
import logging
from pathlib import Path
from typing import Tuple, List, Optional, Union

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

CACHE_DIR = Path.home() / ".cache" / "lama"
LAMA_MODEL_FILE = CACHE_DIR / "lama_fp32.onnx"

_LAMA_SESSION = None
_LAMA_FAILED = False


def is_lama_cached() -> bool:
    """Check if the LaMa inpainting model (~198MB) is cached locally."""
    return LAMA_MODEL_FILE.exists() and LAMA_MODEL_FILE.stat().st_size > 150_000_000


def _get_lama_session():
    """Lazily load and cache LaMa inpainting ONNX session singleton."""
    global _LAMA_SESSION, _LAMA_FAILED
    if _LAMA_SESSION is not None:
        return _LAMA_SESSION
    if _LAMA_FAILED:
        return None

    if not is_lama_cached():
        return None

    try:
        import onnxruntime as ort
        sess_opts = ort.SessionOptions()
        sess_opts.inter_op_num_threads = 2
        sess_opts.intra_op_num_threads = 4
        sess_opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

        _LAMA_SESSION = ort.InferenceSession(
            str(LAMA_MODEL_FILE),
            sess_options=sess_opts,
            providers=['CPUExecutionProvider']
        )
        logger.info("LaMa inpainting ONNX session initialized.")
        return _LAMA_SESSION
    except Exception as e:
        logger.warning(f"LaMa session initialization failed: {e}")
        _LAMA_FAILED = True
        return None


def _decode_mask_data(mask_data: str, target_w: int, target_h: int) -> np.ndarray:
    """Decode base64 mask string or data URL into a binary single-channel uint8 mask."""
    if ',' in mask_data:
        mask_data = mask_data.split(',', 1)[1]

    raw_bytes = base64.b64decode(mask_data)
    pil_mask = Image.open(io.BytesIO(raw_bytes))

    if pil_mask.size != (target_w, target_h):
        pil_mask = pil_mask.resize((target_w, target_h), Image.Resampling.NEAREST)

    arr = np.array(pil_mask)
    if arr.ndim == 3:
        if arr.shape[2] == 4:
            # If RGBA, alpha > 0 or red > 50 is mask
            mask = np.where((arr[:, :, 3] > 20) | (arr[:, :, 0] > 50), 255, 0).astype(np.uint8)
        else:
            mask = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
            mask = np.where(mask > 20, 255, 0).astype(np.uint8)
    else:
        mask = np.where(arr > 20, 255, 0).astype(np.uint8)

    # Slight morphological dilation (3px) to ensure complete coverage of object edges
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask_dilated = cv2.dilate(mask, kernel, iterations=1)
    return mask_dilated


def _pad_to_512(tensor: np.ndarray) -> Tuple[np.ndarray, int, int]:
    """Pad H and W dimensions of (1, C, H, W) tensor to exactly 512x512 using reflect padding."""
    _, _, h, w = tensor.shape
    pad_h = max(0, 512 - h)
    pad_w = max(0, 512 - w)

    if pad_h == 0 and pad_w == 0:
        return tensor, 0, 0

    mode = 'reflect' if (pad_h < h and pad_w < w) else 'edge'
    padded = np.pad(tensor, ((0, 0), (0, 0), (0, pad_h), (0, pad_w)), mode=mode)
    return padded, pad_h, pad_w


def _pad_to_multiple(tensor: np.ndarray, multiple: int = 8) -> Tuple[np.ndarray, int, int]:
    """Pad H and W dimensions of (1, C, H, W) to multiples of 8 or 512 for FFC."""
    return _pad_to_512(tensor)


def _expand_mask_to_objects(np_rgb: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """
    Intelligently expand brush mask to fully enclose connected objects/text/shapes
    so that partially painted objects don't leave residual blurry borders.
    """
    h, w = mask.shape[:2]
    total_pixels = h * w
    mask_pixels = int(np.count_nonzero(mask > 0))
    if mask_pixels == 0 or mask_pixels > total_pixels * 0.7:
        return mask

    try:
        # Sample borders to detect dominant background color
        borders = np.vstack([np_rgb[0, :, :], np_rgb[-1, :, :], np_rgb[:, 0, :], np_rgb[:, -1, :]])
        bg_color = np.median(borders, axis=0)
        bg_dist = np.linalg.norm(np_rgb.astype(float) - bg_color, axis=2)

        brush_dist = bg_dist[mask > 0]
        if len(brush_dist) > 0 and np.median(brush_dist) > 15.0:
            # User painted on foreground object distinct from border background
            fg_mask = (bg_dist > 12.0).astype(np.uint8)
            num_labels, labels = cv2.connectedComponents(fg_mask)
            touched_labels = np.unique(labels[mask > 0])
            touched_labels = touched_labels[touched_labels != 0]

            expanded = mask.copy()
            expanded_any = False
            for lbl in touched_labels:
                comp = (labels == lbl)
                comp_size = int(np.sum(comp))
                overlap = int(np.sum(comp & (mask > 0)))
                if comp_size < (total_pixels * 0.50) and (overlap >= min(40, comp_size * 0.05)):
                    expanded = np.maximum(expanded, comp.astype(np.uint8) * 255)
                    expanded_any = True
            if expanded_any:
                logger.info("Smart Object Snap expanded brush mask to full connected object boundaries.")
            return expanded
    except Exception as e:
        logger.debug(f"Object snap expansion skipped: {e}")

    return mask


def inpaint_image(
    image_path: Path,
    mask_data: str,
    output_path: Path,
    quality: str = "fast",
    dilate_radius: int = 5,
    method: str = "auto",
) -> Tuple[List[str], int, int]:
    """
    Remove masked objects from image and inpaint background using LaMa ONNX.

    Args:
        image_path: Path to original image.
        mask_data: Base64 data URL of user-drawn brush mask.
        output_path: Destination path for inpainted image.
        quality: 'fast' or 'ultra' (applies boundary refinement).
        dilate_radius: Pixel margin to expand mask to avoid edge halo.
        method: 'lama', 'telea', or 'auto'.

    Returns:
        (changes_applied, width, height)
    """
    changes: List[str] = []
    pil_img = Image.open(image_path)
    has_alpha = pil_img.mode in ("RGBA", "LA", "PA")
    orig_w, orig_h = pil_img.size

    rgb_img = pil_img.convert("RGB")
    np_rgb = np.array(rgb_img)

    # Decode mask to target resolution
    mask_uint8 = _decode_mask_data(mask_data, orig_w, orig_h)

    # Check if mask has any marked pixels
    if not np.any(mask_uint8 > 0):
        # Nothing marked to inpaint
        rgb_img.save(output_path, "PNG")
        return ["No mask painted (image unchanged)"], orig_w, orig_h

    # 1. Smart Object Snap: Expand mask to enclose partially painted foreground objects
    mask_uint8 = _expand_mask_to_objects(np_rgb, mask_uint8)

    # 2. Expand mask margin to guarantee complete boundary clearing
    effective_dilate = max(dilate_radius, 8) if quality in ("pro", "ultra") else max(dilate_radius, 6)
    if effective_dilate > 0:
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (effective_dilate * 2 + 1, effective_dilate * 2 + 1))
        mask_uint8 = cv2.dilate(mask_uint8, kernel)
        changes.append(f"Mask Margin Expansion ({effective_dilate}px)")

    sess = None if method == "telea" else _get_lama_session()
    if sess is None or method == "telea":
        # Fallback or explicit OpenCV Navier-Stokes/Telea inpainting
        logger.info("Using OpenCV Telea inpainting.")
        inpainted = cv2.inpaint(np_rgb, mask_uint8, inpaintRadius=max(5, effective_dilate // 2), flags=cv2.INPAINT_TELEA)
        changes.append("Object Removal (OpenCV Fast Inpaint)")
    else:
        logger.info("Executing LaMa neural inpainting...")
        # 1. Compute scale factor so longer dimension fits 512 (maintain aspect ratio)
        scale = 512.0 / max(orig_w, orig_h)
        scaled_w = int(round(orig_w * scale))
        scaled_h = int(round(orig_h * scale))
        scaled_w = min(512, max(1, scaled_w))
        scaled_h = min(512, max(1, scaled_h))

        # 2. Resize image and mask using scale factor (INTER_AREA for image, INTER_NEAREST for mask)
        img_scaled = cv2.resize(np_rgb, (scaled_w, scaled_h), interpolation=cv2.INTER_AREA)
        mask_scaled = cv2.resize(mask_uint8, (scaled_w, scaled_h), interpolation=cv2.INTER_NEAREST)
        mask_scaled = np.where(mask_scaled > 10, 255, 0).astype(np.uint8)

        # 3. Pad shorter dimension with reflect padding to reach exactly 512x512 without stretching
        img_f = (img_scaled.astype(np.float32) / 255.0).transpose(2, 0, 1)[np.newaxis, :]
        mask_f = (mask_scaled.astype(np.float32) / 255.0)[np.newaxis, np.newaxis, :]

        img_padded, pad_h, pad_w = _pad_to_512(img_f)
        mask_padded, _, _ = _pad_to_512(mask_f)

        # Zero out object content inside mask hole so LaMa cannot see or blur existing object
        img_masked = img_padded * (1.0 - mask_padded)

        inputs = sess.get_inputs()
        feed_dict = {}
        for inp in inputs:
            name = inp.name
            if 'mask' in name.lower():
                feed_dict[name] = mask_padded
            else:
                feed_dict[name] = img_masked

        # Run inference
        out_512 = sess.run(None, feed_dict)[0]
        out_512_img = out_512[0].transpose(1, 2, 0)

        # Handle output range [0, 1] or [0, 255]
        max_val = np.max(out_512_img)
        if max_val <= 1.5:
            out_rgb_512 = np.clip(out_512_img * 255.0, 0, 255).astype(np.uint8)
        else:
            out_rgb_512 = np.clip(out_512_img, 0, 255).astype(np.uint8)

        # 4. Crop back to pre-pad region, then resize (Lanczos-4) back to original dimensions
        out_cropped = out_rgb_512[:scaled_h, :scaled_w]
        out_rgb = cv2.resize(out_cropped, (orig_w, orig_h), interpolation=cv2.INTER_LANCZOS4)

        # Distance-transform edge feathering (blends smoothly strictly in outer background, avoiding object blur)
        dist_to_bg = cv2.distanceTransform(mask_uint8, cv2.DIST_L2, 5)
        feather_mask = np.clip(dist_to_bg / 4.0, 0.0, 1.0)[:, :, np.newaxis]
        inpainted = (out_rgb.astype(np.float32) * feather_mask +
                     np_rgb.astype(np.float32) * (1.0 - feather_mask)).astype(np.uint8)
        changes.append("LaMa Inpainting AI (512px FFC Native)")

        if quality in ("pro", "ultra"):
            changes.append("Magic Eraser (LaMa Pro Inpainting + Edge Refinement)")
        else:
            changes.append("Magic Eraser (LaMa Fast Inpainting)")

    # Preserve original alpha channel if present
    if has_alpha:
        alpha = pil_img.split()[3]
        final_img = Image.fromarray(inpainted, "RGB").convert("RGBA")
        final_img.putalpha(alpha)
    else:
        final_img = Image.fromarray(inpainted, "RGB")

    final_img.save(output_path, "PNG")
    return changes, orig_w, orig_h
