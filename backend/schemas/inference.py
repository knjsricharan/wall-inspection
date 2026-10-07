"""Schemas for the optional local YOLOv8-seg inference endpoint."""

from typing import Literal

from pydantic import BaseModel, Field


class InferenceRequest(BaseModel):
    """A processed image emitted by the existing preprocessing pipeline."""

    processed_image_url: str = Field(
        ...,
        description="Backend-relative /uploads URL returned by /api/process-image.",
    )


class BoundingBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float


class SegmentationMask(BaseModel):
    """Polygon in processed-image pixel coordinates, plus the saved binary mask."""

    polygon: list[list[float]]
    mask_url: str


class Detection(BaseModel):
    class_id: int
    class_name: str
    confidence: float
    bounding_box: BoundingBox
    segmentation_mask: SegmentationMask


class InferenceResponse(BaseModel):
    status: Literal["completed", "model_not_available"]
    message: str
    model_path: str
    overlay_image_url: str | None = None
    detections: list[Detection] = []
