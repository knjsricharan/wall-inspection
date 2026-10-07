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
    length_mm: float | None = None
    length_cm: float | None = None
    width_mm: float | None = None
    width_cm: float | None = None
    max_width_mm: float | None = None
    max_width_cm: float | None = None
    area_mm2: float | None = None
    area_cm2: float | None = None


class MeasurementSummary(BaseModel):
    detected_cracks: int = 0
    total_area_px2: int = 0
    total_length_px: float = 0.0
    max_width_px: float = 0.0
    measurement_unit: str = "pixel"
    calibrated: bool = False
    total_area_mm2: float | None = None
    total_area_cm2: float | None = None
    total_length_mm: float | None = None
    total_length_cm: float | None = None
    max_width_mm: float | None = None
    max_width_cm: float | None = None


class CalibrationInfo(BaseModel):
    marker_detected: bool
    marker_id: int | None = None
    marker_size_mm: float
    marker_pixel_size: float | None = None
    pixels_per_mm: float | None = None
    calibrated: bool
    measurement_unit: str
    calibration_status: str
    calibration_quality: str


class ConditionAssessment(BaseModel):
    condition: str
    condition_score: float
    calibrated: bool
    measurement_mode: str
    preliminary: bool
    assessment_type: str
    threshold_profile: str
    threshold_configuration: dict
    basis: list[str]
    reasons: list[str]


class InferenceResponse(BaseModel):
    status: Literal["completed", "model_not_available"]
    message: str
    model_path: str
    overlay_image_url: str | None = None
    measurement_overlay_url: str | None = None
    measurement_summary: MeasurementSummary | None = None
    calibration: CalibrationInfo | None = None
    calibration_overlay_url: str | None = None
    condition_assessment: ConditionAssessment | None = None
    detections: list[Detection] = []
