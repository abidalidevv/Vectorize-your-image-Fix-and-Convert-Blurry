"""
VectorForge AI — Pro Super-Resolution Model Engine
Handles loading and inference for the Pro tier super-resolution model.
When the user provides the model weights, they will be loaded here.
If weights/model are not yet installed, gracefully notifies and allows fallback.
"""
import logging
from pathlib import Path
from typing import Tuple, Optional
import numpy as np

logger = logging.getLogger(__name__)

PRO_WEIGHTS_DIR = Path(__file__).parent / "weights"
_PRO_ENHANCER_SESSION = None
_PRO_ENHANCER_INITIALIZED = False


def is_enhancer_pro_available() -> bool:
    """Check if the Pro enhancer model weights are present."""
    # Check weights folder for any onnx or model files
    if not PRO_WEIGHTS_DIR.exists():
        return False
    weights = list(PRO_WEIGHTS_DIR.glob("*.onnx")) + list(PRO_WEIGHTS_DIR.glob("*.pth")) + list(PRO_WEIGHTS_DIR.glob("*.pt"))
    return len(weights) > 0


def get_pro_enhancer_session():
    """Load and cache the Pro Super-Resolution model session."""
    global _PRO_ENHANCER_SESSION, _PRO_ENHANCER_INITIALIZED
    if _PRO_ENHANCER_SESSION is not None:
        return _PRO_ENHANCER_SESSION
    if _PRO_ENHANCER_INITIALIZED:
        return None

    _PRO_ENHANCER_INITIALIZED = True
    if not is_enhancer_pro_available():
        logger.info("Pro enhancer weights not yet found in models_pro/weights.")
        return None

    try:
        import onnxruntime as ort
        weights = list(PRO_WEIGHTS_DIR.glob("*.onnx"))
        if weights:
            model_path = weights[0]
            opts = ort.SessionOptions()
            opts.inter_op_num_threads = 2
            opts.intra_op_num_threads = 4
            _PRO_ENHANCER_SESSION = ort.InferenceSession(
                str(model_path),
                sess_options=opts,
                providers=['CPUExecutionProvider']
            )
            logger.info(f"Pro Enhancer model loaded successfully from {model_path.name}")
            return _PRO_ENHANCER_SESSION
    except Exception as e:
        logger.warning(f"Failed to load Pro enhancer model: {e}")
    return None


def enhance_pro(np_rgb: np.ndarray, scale: int) -> Tuple[np.ndarray, str]:
    """
    Run super-resolution inference using the Pro model.
    Falls back gracefully if session is not available.
    """
    sess = get_pro_enhancer_session()
    if sess is None:
        raise RuntimeError("Pro Enhancer model weights not yet configured in models_pro/weights.")

    # Placeholder for model-specific inference logic once user provides model details
    # Runs the loaded ONNX session
    h, w, c = np_rgb.shape
    inp = (np_rgb.astype(np.float32) / 255.0).transpose(2, 0, 1)[np.newaxis, :]
    input_name = sess.get_inputs()[0].name
    out = sess.run(None, {input_name: inp})[0]
    out_rgb = np.clip(out[0].transpose(1, 2, 0) * 255.0, 0, 255).astype(np.uint8)
    return out_rgb, f"Super-Resolution {scale}× (Pro AI Model)"
