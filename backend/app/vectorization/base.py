"""
VectorForge AI — Abstract Vectorization Engine Interface
"""
from abc import ABC, abstractmethod
from pathlib import Path


class AbstractTracer(ABC):
    """Base class for all vectorization engines."""

    @abstractmethod
    def trace(self, image_path: Path, output_svg_path: Path, params: dict) -> dict:
        """
        Trace raster image to SVG.

        Args:
            image_path: Path to input raster image (PNG preferred)
            output_svg_path: Path where SVG should be written
            params: Engine-specific parameters dict

        Returns:
            dict with at minimum: {'success': bool, 'engine': str, 'error': str or None}
        """
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable engine name."""
        ...

    @property
    @abstractmethod
    def supports_color(self) -> bool:
        """Whether this engine supports multi-color tracing."""
        ...
