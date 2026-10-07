from fastapi import APIRouter, HTTPException

from backend.schemas.report import ReportRequest, ReportResponse
from backend.services.report_service import generate_report

router = APIRouter()


@router.post("/generate-report", response_model=ReportResponse)
def create_report(request: ReportRequest) -> ReportResponse:
    try:
        output = generate_report(request)
    except (ImportError, OSError, ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=f"Report generation failed: {exc}") from exc
    return ReportResponse(status="completed", message="Inspection report generated from live pixel measurements.", **output)
