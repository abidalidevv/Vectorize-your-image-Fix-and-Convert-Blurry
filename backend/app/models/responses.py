"""
VectorForge AI — Pydantic Response Models
"""
from typing import Optional, List, Literal
from pydantic import BaseModel


class ImageInfoResponse(BaseModel):
    session_id: str
    filename: str
    width: int
    height: int
    file_size_bytes: int
    format: str
    has_alpha: bool
    mode: str  # RGB, RGBA, L, etc.
    preview_url: str


class ColorInfo(BaseModel):
    hex: str          # "#rrggbb"
    rgb: List[int]    # [r, g, b]
    percentage: float # approximate coverage
    index: int


class AnalysisResponse(BaseModel):
    session_id: str
    recommended_mode: Literal["logo", "photo", "sketch", "bw"]
    confidence: float
    color_count_estimate: int
    dominant_colors: List[ColorInfo]
    is_grayscale: bool
    has_transparency: bool
    edge_density: float       # 0.0 – 1.0
    complexity_score: float   # 0.0 – 1.0
    saturation_mean: float
    notes: str


class PaletteColor(BaseModel):
    index: int
    hex: str
    rgb: List[int]
    percentage: float
    enabled: bool = True
    is_background: bool = False


class QuantizeResponse(BaseModel):
    session_id: str
    num_colors: int
    palette: List[PaletteColor]
    preview_url: str


class SVGStatistics(BaseModel):
    path_count: int
    group_count: int
    color_count: int
    file_size_bytes: int
    width: float
    height: float
    has_viewbox: bool
    contains_raster: bool


class LayerInfo(BaseModel):
    index: int
    color_hex: str
    color_rgb: List[int]
    path_count: int
    visible: bool = True
    label: str


class VectorizeResponse(BaseModel):
    session_id: str
    svg_url: str
    svg_data_url: str  # inline for preview
    stats: SVGStatistics
    layers: List[LayerInfo]
    engine_used: str
    processing_time_ms: int


class PreprocessResponse(BaseModel):
    session_id: str
    preview_url: str
    changes_applied: List[str]


class ExportResponse(BaseModel):
    session_id: str
    download_url: str
    filename: str
    file_size_bytes: int
    format: str
