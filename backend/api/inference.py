"""API endpoint for inference on an already processed local image."""

from fastapi import APIRouter, HTTPException

from backend.schemas.inference import InferenceRequest, InferenceResponse
from backend.services.inference_service import run_inference

router = APIRouter()


@router.post("/run-inference", response_model=InferenceResponse)
async def run_inference_endpoint(request: InferenceRequest):
    try:
        return run_inference(request.processed_image_url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
