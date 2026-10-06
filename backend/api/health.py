"""
API route: health check.
GET /api/health
"""

from fastapi import APIRouter
from backend.core.config import get_settings
from backend.database.supabase_client import check_supabase_connection
from backend.schemas.quality import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check():
    """
    Returns application status and Supabase connectivity.
    """
    settings = get_settings()
    supabase_status = check_supabase_connection()

    return HealthResponse(
        status="ok",
        version=settings.app_version,
        supabase_connected=supabase_status["connected"],
        supabase_note=supabase_status.get("reason"),
    )
