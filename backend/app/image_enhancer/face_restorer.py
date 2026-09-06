"""
VectorForge AI — Face & Old Photo Restoration Engine (GFPGAN v1.4 ONNX)
Reconstructs low-resolution, blurred, or corrupted human faces into crisp,
photorealistic details using GFPGAN v1.4 and OpenCV YuNet landmark detector.
"""
import logging
from pathlib import Path
from typing import Tuple, List, Optional

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

CACHE_DIR = Path.home() / ".cache" / "gfpgan"
GFPGAN_MODEL_FILE = CACHE_DIR / "GFPGANv1.4.onnx"
YUNET_MODEL_FILE = CACHE_DIR / "face_detection_yunet.onnx"

_GFPGAN_SESSION = None
_YUNET_DETECTOR = None


def is_gfpgan_cached() -> bool:
    """Check if the GFPGAN v1.4 model (~324MB) is cached locally."""
    return GFPGAN_MODEL_FILE.exists() and GFPGAN_MODEL_FILE.stat().st_size > 200_000_000


def is_yunet_cached() -> bool:
    """Check if the YuNet face detector model (~227KB) is cached locally."""
    return YUNET_MODEL_FILE.exists() and YUNET_MODEL_FILE.stat().st_size > 100_000


def _get_gfpgan_session():
    """Lazily initialize and cache GFPGAN v1.4 ONNX session singleton."""
    global _GFPGAN_SESSION
    if _GFPGAN_SESSION is not None:
        return _GFPGAN_SESSION

    if not is_gfpgan_cached():
        return None

    try:
        import onnxruntime as ort
        sess_opts = ort.SessionOptions()
        sess_opts.inter_op_num_threads = 2
        sess_opts.intra_op_num_threads = 4
        _GFPGAN_SESSION = ort.InferenceSession(
            str(GFPGAN_MODEL_FILE),
            sess_options=sess_opts,
            providers=['CPUExecutionProvider']
        )
        logger.info("GFPGAN v1.4 session initialized successfully.")
        return _GFPGAN_SESSION
    except Exception as e:
        logger.warning(f"Failed to initialize GFPGAN session: {e}")
        return None


def _get_face_detector(img_w: int, img_h: int):
    """Lazily initialize OpenCV YuNet face detector."""
    global _YUNET_DETECTOR
    if not is_yunet_cached():
        return None

    try:
        if _YUNET_DETECTOR is None:
            _YUNET_DETECTOR = cv2.FaceDetectorYN.create(
                str(YUNET_MODEL_FILE),
                "",
                (img_w, img_h),
                score_threshold=0.5,
                nms_threshold=0.3,
                top_k=50
            )
        else:
            _YUNET_DETECTOR.setInputSize((img_w, img_h))
        return _YUNET_DETECTOR
    except Exception as e:
        logger.warning(f"Failed to initialize YuNet face detector: {e}")
        return None


def _align_and_crop_face(
    img_bgr: np.ndarray,
    box: np.ndarray,
    landmarks: Optional[np.ndarray] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Crop face with smooth margin and generate inverse transform matrix for seamless blending.
    Target canonical face size is 512x512.
    """
    h, w = img_bgr.shape[:2]
    x, y, bw, bh = box[:4].astype(int)

    # Add 40% contextual margin around detected face box
    margin_x = int(bw * 0.4)
    margin_y = int(bh * 0.4)

    cx = x + bw / 2.0
    cy = y + bh / 2.0
    half_size = max(bw + margin_x * 2, bh + margin_y * 2) / 2.0

    src_pts = np.float32([
        [cx - half_size, cy - half_size],
        [cx + half_size, cy - half_size],
        [cx + half_size, cy + half_size]
    ])

    dst_pts = np.float32([
        [0, 0],
        [512, 0],
        [512, 512]
    ])

    M = cv2.getAffineTransform(src_pts, dst_pts)
    M_inv = cv2.getAffineTransform(dst_pts, src_pts)

    face_512 = cv2.warpAffine(img_bgr, M, (512, 512), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REFLECT)
    return face_512, M_inv


def restore_faces(
    img_rgb: np.ndarray,
    fidelity: float = 0.8
) -> Tuple[np.ndarray, int]:
    """
    Detect human faces in the image and restore facial features using GFPGAN v1.4.

    Args:
        img_rgb: Input image in RGB uint8 format [H, W, 3].
        fidelity: Blending weight between restored and original face (0.1 to 1.0).

    Returns:
        (restored_rgb, faces_restored_count)
    """
    sess = _get_gfpgan_session()
    if sess is None:
        logger.warning("GFPGAN session unavailable; skipping face restoration.")
        return img_rgb, 0

    h, w = img_rgb.shape[:2]
    img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)

    # 1. Detect faces using YuNet
    detector = _get_face_detector(w, h)
    faces = None
    if detector is not None:
        try:
            _, faces = detector.detect(img_bgr)
        except Exception as e:
            logger.warning(f"YuNet detection failed: {e}")

    # Fallback: If no detector or no faces detected, check center region
    if faces is None or len(faces) == 0:
        logger.info("No faces detected in image.")
        return img_rgb, 0

    input_name = sess.get_inputs()[0].name
    faces_count = 0
    output_bgr = img_bgr.copy()

    for face in faces:
        box = face[:4]
        landmarks = face[4:14].reshape(5, 2) if len(face) >= 14 else None

        # Align to 512x512
        face_512, M_inv = _align_and_crop_face(output_bgr, box, landmarks)

        # Convert to RGB float32 in [-1, 1] range for GFPGAN
        face_rgb = cv2.cvtColor(face_512, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        face_norm = (face_rgb - 0.5) / 0.5
        inp = face_norm.transpose(2, 0, 1)[np.newaxis, :]

        try:
            # Run inference
            out = sess.run(None, {input_name: inp})[0]
            restored_rgb = np.clip((out[0].transpose(1, 2, 0) + 1.0) * 0.5 * 255.0, 0, 255).astype(np.uint8)
            restored_bgr = cv2.cvtColor(restored_rgb, cv2.COLOR_RGB2BGR)

            # Fidelity blending
            if fidelity < 1.0:
                restored_bgr = cv2.addWeighted(restored_bgr, fidelity, face_512, 1.0 - fidelity, 0.0)

            # Create soft radial feather mask for seamless border integration
            mask_512 = np.zeros((512, 512), dtype=np.float32)
            cv2.circle(mask_512, (256, 256), 220, 1.0, -1)
            mask_512 = cv2.GaussianBlur(mask_512, (101, 101), 0)

            # Warp restored face and feathered mask back to image coordinates
            warped_face = cv2.warpAffine(restored_bgr, M_inv, (w, h), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REFLECT)
            warped_mask = cv2.warpAffine(mask_512, M_inv, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
            warped_mask_3c = np.repeat(warped_mask[:, :, np.newaxis], 3, axis=2)

            # Blend into output image
            output_bgr = (warped_face.astype(np.float32) * warped_mask_3c +
                          output_bgr.astype(np.float32) * (1.0 - warped_mask_3c)).astype(np.uint8)
            faces_count += 1
        except Exception as e:
            logger.warning(f"GFPGAN inference error on face: {e}")

    restored_rgb_out = cv2.cvtColor(output_bgr, cv2.COLOR_BGR2RGB)
    return restored_rgb_out, faces_count
