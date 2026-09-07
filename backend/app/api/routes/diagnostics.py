"""
VectorForge AI — Diagnostics & System Health API Route
Provides deep runtime telemetry: hardware providers, model cache status,
edge post-processing pipelines, memory metrics, and engine status.
"""
import os
import sys
import platform
import logging
from pathlib import Path
from typing import Dict, Any, List

from fastapi import APIRouter

router = APIRouter()
logger = logging.getLogger(__name__)


def _get_system_memory() -> Dict[str, Any]:
    """Retrieve system memory metrics safely cross-platform."""
    try:
        if sys.platform == "win32":
            import ctypes
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]
            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
            total_gb = round(stat.ullTotalPhys / (1024 ** 3), 2)
            avail_gb = round(stat.ullAvailPhys / (1024 ** 3), 2)
            used_pct = stat.dwMemoryLoad
            return {"total_gb": total_gb, "available_gb": avail_gb, "used_percent": used_pct}
        elif sys.platform.startswith("linux"):
            meminfo: Dict[str, float] = {}
            meminfo_file = Path("/proc/meminfo")
            if meminfo_file.exists():
                with open(meminfo_file, "r", encoding="utf-8") as f:
                    for line in f:
                        parts = line.split(":")
                        if len(parts) == 2:
                            key = parts[0].strip()
                            val_str = parts[1].strip().split()[0]
                            try:
                                meminfo[key] = float(val_str)
                            except ValueError:
                                pass
                if "MemTotal" in meminfo and "MemAvailable" in meminfo:
                    total_kb = meminfo["MemTotal"]
                    avail_kb = meminfo["MemAvailable"]
                    total_gb = round(total_kb / (1024 * 1024), 2)
                    avail_gb = round(avail_kb / (1024 * 1024), 2)
                    used_percent = round(((total_kb - avail_kb) / total_kb) * 100.0, 1)
                    return {"total_gb": total_gb, "available_gb": avail_gb, "used_percent": used_percent}
    except Exception as e:
        logger.debug(f"Memory probe fallback: {e}")
    return {"total_gb": None, "available_gb": None, "used_percent": None}


def _check_file(path_obj: Path, min_bytes: int = 100_000) -> Dict[str, Any]:
    """Inspect model file on disk."""
    if path_obj.exists() and path_obj.stat().st_size > min_bytes:
        size_bytes = path_obj.stat().st_size
        return {
            "cached": True,
            "path": str(path_obj),
            "size_mb": round(size_bytes / (1024 * 1024), 2),
            "size_bytes": size_bytes,
        }
    return {
        "cached": False,
        "path": str(path_obj),
        "size_mb": 0.0,
        "size_bytes": 0,
    }


@router.get("/diagnostics", tags=["diagnostics"])
async def get_system_diagnostics():
    """
    Comprehensive system health, hardware status, and model verification.
    Used by diagnose.html and DevOps telemetry.
    """
    from core.config import settings
    from core.session import session_manager
    from bg_remover.engine import (
        _is_rembg_cached,
        _is_birefnet_cached,
    )
    from image_enhancer.engine import (
        _is_realesrgan_fast_cached,
        _is_realesrgan_ultra_cached,
        FAST_MODEL_FILE,
        ULTRA_MODEL_FILE,
    )
    from image_enhancer.face_restorer import (
        is_gfpgan_cached,
        is_yunet_cached,
        GFPGAN_MODEL_FILE,
        YUNET_MODEL_FILE,
    )
    from magic_eraser.engine import (
        is_lama_cached,
        LAMA_MODEL_FILE,
    )

    # Resolve paths
    isnet_candidates = [
        Path.home() / ".rembg" / "models" / "isnet-general-use" / "isnet-general-use.onnx",
        Path.home() / ".u2net" / "isnet-general-use.onnx",
    ]
    isnet_path = next((p for p in isnet_candidates if p.exists()), isnet_candidates[0])

    birefnet_candidates = [
        Path.home() / ".rembg" / "models" / "birefnet-general-lite" / "birefnet-general-lite.onnx",
        Path.home() / ".u2net" / "birefnet-general-lite.onnx",
        Path.home() / ".rembg" / "models" / "birefnet-general" / "birefnet-general.onnx",
        Path.home() / ".u2net" / "birefnet-general.onnx",
    ]
    birefnet_path = next((p for p in birefnet_candidates if p.exists()), birefnet_candidates[0])

    isnet_info = _check_file(isnet_path, 10_000_000)
    isnet_info["cached"] = _is_rembg_cached()

    birefnet_info = _check_file(birefnet_path, 100_000_000)
    birefnet_info["cached"] = _is_birefnet_cached()

    realesr_fast_info = _check_file(FAST_MODEL_FILE, 1_000_000)
    realesr_fast_info["cached"] = _is_realesrgan_fast_cached()

    realesr_ultra_info = _check_file(ULTRA_MODEL_FILE, 50_000_000)
    realesr_ultra_info["cached"] = _is_realesrgan_ultra_cached()

    gfpgan_info = _check_file(GFPGAN_MODEL_FILE, 200_000_000)
    gfpgan_info["cached"] = is_gfpgan_cached()

    yunet_info = _check_file(YUNET_MODEL_FILE, 100_000)
    yunet_info["cached"] = is_yunet_cached()

    lama_info = _check_file(LAMA_MODEL_FILE, 150_000_000)
    lama_info["cached"] = is_lama_cached()

    # Providers
    providers: List[str] = []
    ort_version = "unavailable"
    try:
        import onnxruntime as ort
        providers = ort.get_available_providers()
        ort_version = getattr(ort, "__version__", "unknown")
    except Exception:
        pass

    # OpenCV status
    cv2_version = "unavailable"
    try:
        import cv2
        cv2_version = cv2.__version__
    except Exception:
        pass

    # VTracer status
    vtracer_status = "available"
    try:
        import vtracer
    except Exception:
        vtracer_status = "not installed"

    mem = _get_system_memory()

    # Calculate overall health
    all_models_cached = (
        isnet_info["cached"]
        and birefnet_info["cached"]
        and realesr_fast_info["cached"]
        and realesr_ultra_info["cached"]
    )
    system_status = "optimal" if all_models_cached else "ready_with_fallbacks"

    return {
        "status": "ok",
        "system_health": system_status,
        "service": "VectorForge AI",
        "version": "1.1.0",
        "platform": {
            "os": platform.system(),
            "os_release": platform.release(),
            "os_version": platform.version(),
            "architecture": platform.machine(),
            "python": sys.version.split()[0],
            "cpu_cores": os.cpu_count(),
            "memory": mem,
        },
        "onnx_runtime": {
            "version": ort_version,
            "providers": providers,
            "hardware_acceleration": any("CUDA" in p or "Dml" in p or "Tensorrt" in p for p in providers),
            "memory_arena_optimized": True,
        },
        "libraries": {
            "opencv": cv2_version,
            "vtracer": vtracer_status,
        },
        "models": {
            "bg_remover": {
                "fast": {
                    "model_name": "isnet-general-use",
                    "status": "cached" if isnet_info["cached"] else "missing",
                    "file_path": isnet_info["path"],
                    "size_mb": isnet_info["size_mb"],
                    "expected_mb": 178.6,
                    "tier": "Fast (Default)",
                    "description": "General-use high-contrast boundary segmentation",
                },
                "ultra": {
                    "model_name": "birefnet-general",
                    "status": "cached" if birefnet_info["cached"] else "missing (will fallback to Fast)",
                    "file_path": birefnet_info["path"],
                    "size_mb": birefnet_info["size_mb"],
                    "expected_mb": 972.7,
                    "tier": "Ultra (Pro Quality)",
                    "description": "Bilateral Reference Network for hair, fur, and intricate semi-transparent edges",
                },
                "features": [
                    "Defringe Halo Choke via cv2.erode (elliptical kernel k=1..9)",
                    "Physical Alpha-Unmixing Color Decontamination [true_fg = (obs - bg*(1-a))/a]",
                    "Gaussian Feathering smoothing transition",
                    "Zero-Arena ONNX Allocation for stable Windows CPU execution",
                ],
            },
            "image_enhancer": {
                "fast": {
                    "model_name": "realesr-general-x4v3",
                    "status": "cached" if realesr_fast_info["cached"] else "missing (will fallback to Lanczos-4)",
                    "file_path": realesr_fast_info["path"],
                    "size_mb": realesr_fast_info["size_mb"],
                    "expected_mb": 4.9,
                    "tier": "Fast (Default AI)",
                    "description": "Lightweight Real-ESRGAN super-resolution neural network",
                },
                "ultra": {
                    "model_name": "RealESRGAN_x4plus",
                    "status": "cached" if realesr_ultra_info["cached"] else "missing (will fallback to Fast)",
                    "file_path": realesr_ultra_info["path"],
                    "size_mb": realesr_ultra_info["size_mb"],
                    "expected_mb": 67.1,
                    "tier": "Ultra (Pro RRDBNet)",
                    "description": "23-layer Residual-in-Residual Dense Block architecture for maximum vector-ready clarity",
                },
                "pipeline_stages": [
                    "Stage 1: Real-ESRGAN Neural Super-Resolution (Fast: x4v3 / Ultra: x4plus)",
                    "Stage 2: Bilateral Filter (Edge-Preserving Denoising)",
                    "Stage 3: LAB Color Space CLAHE (Contrast-Limited Adaptive Histogram)",
                    "Stage 4: Gaussian High-Pass Unsharp Masking",
                    "Stage 5: Morphological Contour Refinement",
                    "Stage 6: HSV Dynamic Range & Vibrance Optimization",
                    "Stage 7: Optional GFPGAN Face & Eye Restoration",
                ],
            },
            "face_restorer": {
                "gfpgan": {
                    "model_name": "GFPGANv1.4",
                    "status": "cached" if gfpgan_info["cached"] else "missing",
                    "file_path": gfpgan_info["path"],
                    "size_mb": gfpgan_info["size_mb"],
                    "expected_mb": 324.5,
                    "tier": "Face Restoration AI",
                    "description": "Generative Facial Prior GAN for blind face restoration and eye detail reconstruction",
                },
                "detector": {
                    "model_name": "YuNet",
                    "status": "cached" if yunet_info["cached"] else "missing",
                    "file_path": yunet_info["path"],
                    "size_mb": yunet_info["size_mb"],
                    "expected_mb": 0.23,
                    "tier": "Facial Landmark Detector",
                    "description": "5-point facial landmark detector for affine alignment (<3ms inference)",
                },
            },
            "magic_eraser": {
                "lama": {
                    "model_name": "LaMa-ONNX",
                    "status": "cached" if lama_info["cached"] else "missing",
                    "file_path": lama_info["path"],
                    "size_mb": lama_info["size_mb"],
                    "expected_mb": 198.4,
                    "tier": "Object Removal & Inpainting AI",
                    "description": "Large Mask Inpainting with Fast Fourier Convolutions (FFC) for high-resolution background synthesis",
                },
            },
        },
        "storage": {
            "temp_dir": str(settings.temp_dir),
            "temp_exists": settings.temp_dir.exists(),
            "active_sessions": len(session_manager._sessions),
        },
        "pre_download_command": "python scripts/download_pro_models.py --all",
    }
