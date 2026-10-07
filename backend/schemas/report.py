"""Request and response contracts for live pixel-based inspection reports."""

from pydantic import BaseModel, Field

from backend.schemas.inference import InferenceResponse


class ReportRequest(BaseModel):
    image_reference: str | None = None
    original_image_url: str | None = None
    processed_image_url: str | None = None
    quality_status: str = "unknown"
    processing_status: str = "completed"
    inference: InferenceResponse


class ReportResponse(BaseModel):
    status: str
    report_id: str
    docx_url: str
    pdf_url: str
    png_url: str
    message: str = Field(..., description="Report generation status")
