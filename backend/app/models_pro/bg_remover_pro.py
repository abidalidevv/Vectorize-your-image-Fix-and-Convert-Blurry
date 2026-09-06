"""
VectorForge AI — Pro Background Remover Model Engine
Handles loading and inference for the Pro tier background matting model.
When the user provides the model weights, they will be loaded here.
If weights/model are not yet installed, gracefully notifies and allows fallback.
"""
import logging
from pathlib import Path
from typing import Optional
from PIL import Image

logger = logging.getLogger(__name__)

PRO_WEIGHTS_DIR = Path(__file__).parent / "weights"
_PRO_BG_SESSION = None
_PRO_BG_INITIALIZED = False


def is_bg_remover_pro_available() -> bool:
    """Check if the Pro background remover model weights are present."""
    if not PRO_WEIGHTS_DIR.exists():
        return False
    # Check for dedicated pro bg model weights
    weights = [
        p for p in (list(PRO_WEIGHTS_DIR.glob("*.onnx")) + list(PRO_WEIGHTS_DIR.glob("*.pth")) + list(PRO_WEIGHTS_DIR.glob("*.pt")))
        if "enhance" not in p.name.lower() and "esr" not in p.name.lower()
    ]
    return len(weights) > 0


def get_pro_bg_session():
    """Load and cache the Pro Background Remover model session."""
    global _PRO_BG_SESSION, _PRO_BG_INITIALIZED
    if _PRO_BG_SESSION is not None:
        return _PRO_BG_SESSION
    if _PRO_BG_INITIALIZED:
        return None

    _PRO_BG_INITIALIZED = True
    if not is_bg_remover_pro_available():
        logger.info("Pro background remover weights not yet found in models_pro/weights.")
        return None

    try:
        import onnxruntime as ort
        weights = [
            p for p in PRO_WEIGHTS_DIR.glob("*.onnx")
            if "enhance" not in p.name.lower() and "esr" not in p.name.lower()
        ]
        if weights:
            model_path = weights[0]
            opts = ort.SessionOptions()
            _PRO_BG_SESSION = ort.InferenceSession(
                str(model_path),
                sess_options=opts,
                providers=['CPUExecutionProvider']
            )
            logger.info(f"Pro Background Remover model loaded successfully from {model_path.name}")
            return _PRO_BG_SESSION
    except Exception as e:
        logger.warning(f"Failed to load Pro background remover model: {e}")
    return None


def remove_bg_pro(img: Image.Image) -> Optional[Image.Image]:
    """
    Run background removal inference using the Pro model.
    Returns the RGBA cutout PIL image with alpha channel.
    """
    sess = get_pro_bg_session()
    if sess is None:
        return None

    # Placeholder for model-specific inference logic once user provides model details
    return None
