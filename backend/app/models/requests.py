"""
VectorForge AI — Pydantic Request Models
"""
from typing import Optional, Literal
from pydantic import BaseModel, Field


class PreprocessParams(BaseModel):
    session_id: str

    # Noise reduction
    denoise_enabled: bool = False
    denoise_strength: float = Field(default=3.0, ge=1.0, le=20.0)

    # Sharpening / blur
    sharpen_enabled: bool = False
    sharpen_strength: float = Field(default=0.5, ge=0.0, le=2.0)

    # Basic adjustments
    contrast: float = Field(default=1.0, ge=0.1, le=3.0)
    brightness: float = Field(default=1.0, ge=0.1, le=3.0)
    saturation: float = Field(default=1.0, ge=0.0, le=3.0)

    # Background removal
    bg_removal_enabled: bool = False
    bg_color: Optional[str] = None     # hex color string like "#ffffff"
    bg_tolerance: float = Field(default=30.0, ge=0.0, le=100.0)
    bg_auto_detect: bool = True

    # Anti-alias cleanup
    antialias_cleanup: bool = False


class QuantizeParams(BaseModel):
    session_id: str
    num_colors: int = Field(default=8, ge=2, le=64)
    method: Literal["kmeans", "median_cut", "auto"] = "auto"
    use_preprocessed: bool = True


class VectorizeParams(BaseModel):
    session_id: str
    image_mode: Literal["auto", "logo", "photo", "sketch", "bw"] = "auto"
    quality_preset: Literal["fast", "balanced", "high", "ultra"] = "balanced"
    source_stage: Literal["auto", "original", "preprocessed", "quantized"] = "auto"

    # Tracing parameters
    color_precision: int = Field(default=6, ge=1, le=8)
    layer_difference: int = Field(default=16, ge=1, le=64)
    corner_threshold: float = Field(default=60.0, ge=0.0, le=180.0)
    length_threshold: float = Field(default=4.0, ge=0.5, le=20.0)
    max_iterations: int = Field(default=10, ge=1, le=20)
    splice_threshold: float = Field(default=45.0, ge=0.0, le=180.0)
    filter_speckle: int = Field(default=4, ge=0, le=64)
    curve_fitting: Literal["pixel", "polygon", "spline", "none"] = "spline"

    # Post-processing
    min_area: float = Field(default=4.0, ge=0.0, le=1000.0)
    simplify_tolerance: float = Field(default=0.5, ge=0.0, le=10.0)

    # Mode flags
    group_by_color: bool = True
    remove_background: bool = False
    preserve_fine_lines: bool = True
    hierarchical: Optional[Literal["cutout", "stacked"]] = "stacked"


class ExportSVGParams(BaseModel):
    session_id: str
    optimize: bool = True
    include_metadata: bool = False


class ExportPNGParams(BaseModel):
    session_id: str
    scale: Literal[1, 2, 4, 8] = 1
    background_color: Optional[str] = None  # None = transparent
    dpi: int = Field(default=96, ge=72, le=600)


class AnalyzeParams(BaseModel):
    session_id: str


class EnhanceParams(BaseModel):
    session_id: str
    quality: Literal["fast", "ultra"] = "fast"
    model_tier: Literal["default", "pro"] = "default"
    scale: Literal[1, 2, 4] = 1
    sharpen_strength: float = Field(default=0.8, ge=0.0, le=3.0)
    denoise_strength: float = Field(default=0.0, ge=0.0, le=15.0)
    clahe_enabled: bool = True
    contrast: float = Field(default=1.0, ge=0.2, le=3.0)
    brightness: float = Field(default=1.0, ge=0.2, le=3.0)
    saturation: float = Field(default=1.0, ge=0.0, le=3.0)
    clarity: float = Field(default=0.3, ge=0.0, le=1.5)
    face_restore: bool = False
    face_fidelity: float = Field(default=0.8, ge=0.1, le=1.0)


class RemoveBgParams(BaseModel):
    session_id: str
    quality: Literal["fast", "ultra"] = "fast"
    model_tier: Literal["default", "pro"] = "default"
    engine: Literal["auto", "ai", "color"] = "auto"
    tolerance: float = Field(default=35.0, ge=0.0, le=120.0)
    feather_radius: float = Field(default=1.0, ge=0.0, le=10.0)
    defringe_choke: int = Field(default=1, ge=0, le=5)
    contiguous: bool = False
    bg_type: Literal["transparent", "color", "gradient"] = "transparent"
    bg_color: Optional[str] = "transparent"


class InpaintParams(BaseModel):
    session_id: str
    mask_data: str  # Base64 data URL or PNG of mask
    quality: Literal["fast", "ultra"] = "fast"
    model_tier: Literal["default", "pro"] = "default"
    dilate_radius: int = Field(default=5, ge=0, le=50)
    method: Literal["lama", "telea", "auto"] = "auto"



