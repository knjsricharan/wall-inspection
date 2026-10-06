"""
Image quality check service for AWIS-HM.

Checks:
  - File size
  - Valid/readable image
  - Image dimensions
  - Blur (Laplacian variance)
  - Exposure (mean brightness)
  - Contrast (standard deviation)

Every metric uses a **two-tier** threshold system:
  FAIL tier   — image is genuinely unusable, downstream analysis will break
  WARNING tier — image is usable but imperfect, may benefit from preprocessing

Design rationale
~~~~~~~~~~~~~~~~
Heritage masonry walls are inherently low-texture surfaces.  A smartphone
photo of a relatively uniform plaster or stone wall will routinely produce
Laplacian-variance (blur) scores well below 100 even when the photo is
perfectly focused.  The original single-tier blur threshold of 100 rejected
these usable images.

All thresholds are project-defined provisional values — they are **not**
scientifically validated limits.  They remain fully configurable via
environment variables.

Preprocessing note
~~~~~~~~~~~~~~~~~~
No preprocessing (histogram equalisation, sharpening, etc.) is applied here.
Altering pixel data could create or remove crack features, which would
compromise downstream YOLO detection.  The quality gate only *classifies*
and *advises*.
"""

import io
import logging

import cv2
import numpy as np
from PIL import Image

from backend.core.config import get_settings
from backend.schemas.quality import QualityCheckResponse, QualityMetrics, QualityStatus

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Metric helpers (pure functions, no side-effects)
# ---------------------------------------------------------------------------

def _laplacian_blur_score(gray: np.ndarray) -> float:
    """Return Laplacian variance as a blur indicator.  Lower → more blurred."""
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def _mean_brightness(gray: np.ndarray) -> float:
    return float(np.mean(gray))


def _contrast_std(gray: np.ndarray) -> float:
    return float(np.std(gray))


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_quality_check(file_bytes: bytes, filename: str) -> QualityCheckResponse:
    """
    Run all quality checks on the uploaded image bytes.

    Classification logic
    --------------------
    Each metric is evaluated against two tiers:

        blur_threshold_fail   <  blur_threshold_warn   (lower = worse)
        brightness_low_fail   <  brightness_low_warn   (lower = worse)
        brightness_high_warn  <  brightness_high_fail  (higher = worse)
        contrast_min_fail     <  contrast_min_warn     (lower = worse)

    If *any* metric hits its FAIL tier the overall result is FAIL.
    If *any* metric hits only its WARNING tier the overall result is WARNING.
    Otherwise the result is PASS.

    Returns a QualityCheckResponse with status, metrics, explanation,
    and recommendation.
    """
    settings = get_settings()
    fails: list[str] = []
    warns: list[str] = []

    # --- File size check ---
    file_size_mb = len(file_bytes) / (1024 * 1024)
    if file_size_mb > settings.quality_max_file_mb:
        fails.append(
            f"File size {file_size_mb:.1f} MB exceeds the "
            f"{settings.quality_max_file_mb:.0f} MB limit."
        )

    # --- Readability check ---
    try:
        pil_image = Image.open(io.BytesIO(file_bytes))
        pil_image.verify()
        # Re-open after verify (verify may close the file pointer)
        pil_image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    except Exception as exc:
        logger.warning("Image decode failed for %s: %s", filename, exc)
        return QualityCheckResponse(
            status=QualityStatus.FAIL,
            metrics=QualityMetrics(
                width=0,
                height=0,
                blur_score=0.0,
                brightness_mean=0.0,
                contrast_std=0.0,
                file_size_mb=round(file_size_mb, 2),
            ),
            explanation="The uploaded file could not be read as a valid image.",
            recommendation="Upload a valid JPG or PNG image file.",
        )

    width, height = pil_image.size

    # Convert to OpenCV grayscale for metric computation
    cv_image = np.array(pil_image)
    gray = cv2.cvtColor(cv_image, cv2.COLOR_RGB2GRAY)

    blur_score = _laplacian_blur_score(gray)
    brightness = _mean_brightness(gray)
    contrast = _contrast_std(gray)

    metrics = QualityMetrics(
        width=width,
        height=height,
        blur_score=round(blur_score, 2),
        brightness_mean=round(brightness, 2),
        contrast_std=round(contrast, 2),
        file_size_mb=round(file_size_mb, 2),
    )

    # --- Dimension check (single tier — undersized is always FAIL) ---
    if width < settings.quality_min_width or height < settings.quality_min_height:
        fails.append(
            f"Image resolution {width}x{height} is below the minimum "
            f"{settings.quality_min_width}x{settings.quality_min_height}."
        )

    # --- Blur check (two tiers) ---
    if blur_score < settings.quality_blur_threshold_fail:
        fails.append(
            f"Image is severely blurred (blur score {blur_score:.1f}, "
            f"fail threshold {settings.quality_blur_threshold_fail})."
        )
    elif blur_score < settings.quality_blur_threshold_warn:
        warns.append(
            f"Image may be slightly blurred (blur score {blur_score:.1f}, "
            f"warning threshold {settings.quality_blur_threshold_warn}). "
            "Consider retaking with steadier hold."
        )

    # --- Exposure check (two tiers, low and high) ---
    if brightness < settings.quality_brightness_low_fail:
        fails.append(
            f"Image is severely underexposed (mean brightness {brightness:.1f}, "
            f"fail threshold {settings.quality_brightness_low_fail})."
        )
    elif brightness < settings.quality_brightness_low_warn:
        warns.append(
            f"Image is somewhat dark (mean brightness {brightness:.1f}, "
            f"warning threshold {settings.quality_brightness_low_warn}). "
            "Preprocessing may improve results."
        )
    elif brightness > settings.quality_brightness_high_fail:
        fails.append(
            f"Image is severely overexposed (mean brightness {brightness:.1f}, "
            f"fail threshold {settings.quality_brightness_high_fail})."
        )
    elif brightness > settings.quality_brightness_high_warn:
        warns.append(
            f"Image may be overexposed (mean brightness {brightness:.1f}, "
            f"warning threshold {settings.quality_brightness_high_warn})."
        )

    # --- Contrast check (two tiers) ---
    if contrast < settings.quality_contrast_min_fail:
        fails.append(
            f"Image has extremely low contrast (std deviation {contrast:.1f}, "
            f"fail threshold {settings.quality_contrast_min_fail}). "
            "Damage features are unlikely to be detectable."
        )
    elif contrast < settings.quality_contrast_min_warn:
        warns.append(
            f"Image has low contrast (std deviation {contrast:.1f}, "
            f"warning threshold {settings.quality_contrast_min_warn}). "
            "Results may be affected."
        )

    # --- Determine overall status ---
    if fails:
        status = QualityStatus.FAIL
        explanation = "Image quality check failed. " + " ".join(fails)
        if warns:
            explanation += " Additional notes: " + " ".join(warns)
        recommendation = (
            "Retake the photograph in adequate lighting, hold the camera steady, "
            "and ensure the wall fills most of the frame."
        )
    elif warns:
        status = QualityStatus.WARNING
        explanation = (
            "Image quality check passed with warnings. " + " ".join(warns)
        )
        recommendation = (
            "The image can be processed, but results may be affected. "
            "Consider retaking with better lighting or a steadier hold "
            "if possible."
        )
    else:
        status = QualityStatus.PASS
        explanation = (
            f"Image quality check passed. Resolution {width}x{height}, "
            f"blur score {blur_score:.1f}, brightness {brightness:.1f}, "
            f"contrast {contrast:.1f}."
        )
        recommendation = "Image is suitable for inspection processing."

    return QualityCheckResponse(
        status=status,
        metrics=metrics,
        explanation=explanation,
        recommendation=recommendation,
    )
