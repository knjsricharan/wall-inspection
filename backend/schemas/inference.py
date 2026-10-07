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
    cleaned_mask_url: str | None = None


class Detection(BaseModel):
    detection_id: int | None = None
    class_id: int
    class_name: str
    confidence: float
    bounding_box: BoundingBox
    segmentation_mask: SegmentationMask
    length_px: float | None = None
    width_px: float | None = None
    max_width_px: float | None = None
    area_px2: int | None = None
    orientation_deg: float | None = None
    measurement_unit: str | None = None
    calibrated: bool | None = None


class MeasurementSummary(BaseModel):
    detected_cracks: int = 0
    total_area_px2: int = 0
    total_length_px: float = 0.0
    max_width_px: float = 0.0
    measurement_unit: str = "pixel"
    calibrated: bool = False


class InferenceResponse(BaseModel):
    status: Literal["completed", "model_not_available"]
    message: str
    model_path: str
    overlay_image_url: str | None = None
    measurement_overlay_url: str | None = None
    measurement_summary: MeasurementSummary | None = None
    detections: list[Detection] = []
