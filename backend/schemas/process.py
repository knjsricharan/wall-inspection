from pydantic import BaseModel
from typing import List, Optional
from backend.schemas.quality import QualityCheckResponse

class ProcessMetadata(BaseModel):
    operations_applied: List[str]
    original_size: List[int]
    processed_size: List[int]

class ProcessResponse(BaseModel):
    quality_result: QualityCheckResponse
    original_image_url: str
    processed_image_url: Optional[str]
    metadata: Optional[ProcessMetadata]
