import logging
from fastapi import APIRouter, File, HTTPException, UploadFile
from backend.schemas.process import ProcessResponse
from backend.services.process_service import preprocess_image
from backend.core.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter()

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/jpg", "image/png"}

@router.post("/process-image", response_model=ProcessResponse)
async def process_image_endpoint(image: UploadFile = File(...)):
    """
    Accept an image, run quality checks, and conditionally preprocess it.
    - Fails early if quality is FAIL.
    - Preprocesses PASS/WARNING images.
    Returns processing metadata and urls to original and processed images.
    """
    settings = get_settings()

    if image.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{image.content_type}'. Upload a JPG or PNG image.",
        )

    file_bytes = await image.read()

    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > settings.quality_max_file_mb:
        raise HTTPException(
            status_code=413,
            detail=f"File size {size_mb:.1f} MB exceeds the {settings.quality_max_file_mb:.0f} MB limit.",
        )

    logger.info("Processing image: %s", image.filename)
    result = preprocess_image(file_bytes, image.filename or "upload")
    return result
