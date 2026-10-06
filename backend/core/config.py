"""
Core configuration for AWIS-HM backend.
All settings are loaded from environment variables.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    app_name: str = "AWIS-HM"
    app_version: str = "0.1.0"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS origins — stored and read as a plain string to avoid pydantic-settings
    # JSON-parsing issues with comma-separated list env vars.
    allowed_origins_raw: str = "http://localhost:5173,http://localhost:3000"

    # Supabase
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_key: str = ""

    # Image quality thresholds — two-tier system (fail / warn).
    # All values are project-defined provisional values, NOT scientifically
    # validated limits.  Override via environment variables as needed.
    #
    # Blur  (Laplacian variance):  lower → worse
    #   - Wall surfaces are inherently low-texture; usable smartphone photos
    #     of masonry routinely score 20–80, so the FAIL tier is set low.
    quality_blur_threshold_fail: float = 15.0
    quality_blur_threshold_warn: float = 50.0
    #
    # Dimensions
    quality_min_width: int = 640
    quality_min_height: int = 480
    #
    # File size
    quality_max_file_mb: float = 20.0
    #
    # Brightness (mean pixel value 0-255):
    #   - Low values = underexposed, high values = overexposed
    quality_brightness_low_fail: float = 25.0
    quality_brightness_low_warn: float = 50.0
    quality_brightness_high_warn: float = 220.0
    quality_brightness_high_fail: float = 240.0
    #
    # Contrast (pixel std deviation):
    #   - Very low contrast makes damage features undetectable
    quality_contrast_min_fail: float = 5.0
    quality_contrast_min_warn: float = 15.0

    # Storage
    upload_dir: str = "uploads"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }

    def get_allowed_origins(self) -> list[str]:
        """Return the CORS allowed origins as a list."""
        return [o.strip() for o in self.allowed_origins_raw.split(",") if o.strip()]


@lru_cache()
def get_settings() -> Settings:
    return Settings()
