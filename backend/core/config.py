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

    # YOLOv8 segmentation inference. The checkpoint is deliberately external to
    # the source tree so a trained heritage-masonry model can replace it later.
    model_path: str = "models/best.pt"
    yolo_confidence_threshold: float = 0.25
    yolo_image_size: int = 640

    # Conservative mask cleanup for measurement. These project-defined defaults
    # remove tiny isolated specks and bridge very small gaps without reshaping
    # the crack geometry aggressively.
    mask_min_region_area_px: int = 20
    mask_closing_kernel_size: int = 3
    mask_closing_iterations: int = 1

    # Image-specific physical calibration. The user must include a real marker
    # printed/measured to this size in each image; this is not a universal scale.
    calibration_marker_size_mm: float = 50.0
    calibration_dictionary: str = "DICT_4X4_50"
    calibration_min_marker_side_px: float = 20.0

    # Project-defined prototype condition thresholds. Calibrated values use
    # mm/mm2; uncalibrated values use explicitly separate pixel thresholds.
    condition_width_moderate_mm: float = 1.0
    condition_width_severe_mm: float = 3.0
    condition_area_moderate_mm2: float = 500.0
    condition_area_severe_mm2: float = 2000.0
    condition_length_moderate_mm: float = 100.0
    condition_length_severe_mm: float = 500.0
    condition_width_moderate_px: float = 3.0
    condition_width_severe_px: float = 10.0
    condition_area_moderate_px2: float = 1000.0
    condition_area_severe_px2: float = 5000.0
    condition_length_moderate_px: float = 100.0
    condition_length_severe_px: float = 500.0
    condition_confidence_high: float = 0.75
    condition_confidence_low: float = 0.50
    condition_uncalibrated_supported: bool = True
    condition_mild_min_score: float = 7.5
    condition_moderate_min_score: float = 4.0

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
