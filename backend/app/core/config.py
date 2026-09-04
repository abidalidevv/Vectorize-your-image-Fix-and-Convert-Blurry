"""
VectorForge AI — Application Configuration
"""
from pathlib import Path
from pydantic_settings import BaseSettings  # type: ignore[import]
from pydantic import Field


class Settings(BaseSettings):
    # Application
    app_name: str = "VectorForge AI"
    debug: bool = False

    # File handling
    max_upload_size_mb: int = 50
    max_image_dimension: int = 8000
    allowed_extensions: set[str] = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}
    allowed_mime_types: set[str] = {
        "image/png", "image/jpeg", "image/bmp", "image/webp", "image/x-bmp"
    }

    # Paths
    base_dir: Path = Path(__file__).parent.parent.parent
    temp_dir: Path = Path(__file__).parent.parent / "temp_files"

    # Session
    session_ttl_seconds: int = 3600  # 1 hour

    # Processing limits
    max_colors: int = 64
    min_image_size: int = 8  # pixels

    class Config:
        env_file = ".env"


settings = Settings()
