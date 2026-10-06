"""
Pydantic schemas for image quality check request and response.
"""

from enum import Enum
from pydantic import BaseModel


class QualityStatus(str, Enum):
    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"


class QualityMetrics(BaseModel):
    width: int
    height: int
    blur_score: float
    brightness_mean: float
    contrast_std: float
    file_size_mb: float


class QualityCheckResponse(BaseModel):
    status: QualityStatus
    metrics: QualityMetrics
    explanation: str
    recommendation: str


class HealthResponse(BaseModel):
    status: str
    version: str
    supabase_connected: bool
    supabase_note: str | None = None
