"""
API route: image quality check.
POST /api/quality-check
"""

import logging

from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.core.config import get_settings
from backend.schemas.quality import QualityCheckResponse
from backend.services.quality_service import run_quality_check

logger = logging.getLogger(__name__)

router = APIRouter()

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/jpg", "image/png"}


@router.post("/quality-check", response_model=QualityCheckResponse)
async def quality_check(image: UploadFile = File(...)):
    """
    Accept an image via multipart/form-data and return a quality assessment.

    Checks performed:
      - Valid/readable image
      - Image dimensions
      - Blur (Laplacian variance)
      - Exposure (mean brightness)
      - Contrast (standard deviation)

    Thresholds are configurable provisional values — not scientifically validated limits.
    """
    settings = get_settings()

    # Content-type check
    if image.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{image.content_type}'. Upload a JPG or PNG image.",
        )

    file_bytes = await image.read()

    # File size guard (before full processing)
    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > settings.quality_max_file_mb:
        raise HTTPException(
            status_code=413,
            detail=f"File size {size_mb:.1f} MB exceeds the {settings.quality_max_file_mb:.0f} MB limit.",
        )

    logger.info("Quality check: %s (%.2f MB)", image.filename, size_mb)

    result = run_quality_check(file_bytes, image.filename or "upload")
    return result
