"""
AWIS-HM FastAPI application entry point.
"""

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import get_settings
from backend.api.health import router as health_router
from backend.api.quality import router as quality_router
from backend.api.process import router as process_router
from backend.api.inference import router as inference_router
from fastapi.staticfiles import StaticFiles

# Configure logging — no emojis in log output
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(
    title="AWIS-HM API",
    description="AI-Based Wall Inspection System for Heritage Masonry — backend API.",
    version=settings.app_version,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure upload directory exists before mounting
os.makedirs(settings.upload_dir, exist_ok=True)

# Mount static files for uploads
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

# Register routers
app.include_router(health_router, prefix="/api", tags=["health"])
app.include_router(quality_router, prefix="/api", tags=["quality"])
app.include_router(process_router, prefix="/api", tags=["process"])
app.include_router(inference_router, prefix="/api", tags=["inference"])


logger.info("AWIS-HM backend started — version %s", settings.app_version)
