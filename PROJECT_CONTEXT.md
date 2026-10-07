# PROJECT_CONTEXT

## 1. Project Summary
AWIS-HM (AI-Based Wall Inspection System for Heritage Masonry) is a web-based end-to-end system that accepts a smartphone image of a heritage masonry wall and produces a surface condition inspection result. It uses YOLOv8-seg for damage detection and segmentation, computes crack measurements (length, width, area), scores the condition, and features a RAG (Retrieval-Augmented Generation) decision-support layer to generate evidence-backed inspection reports. It evaluates visible surface damage only.

## 2. Current Architecture
- **Frontend**: React application running on the user's laptop. (Running via Vite dev server)
- **Backend Orchestrator**: FastAPI handling API requests and workflow. (Running via Uvicorn)
- **Image Pipeline**: Quality check and conditional preprocessing implemented using OpenCV.
- **AI Inference**: YOLOv8-seg CPU inference is implemented and runtime verified with a real local crack-segmentation checkpoint.
- **Post-Processing & Measurement**: Not implemented yet.
- **Database**: Supabase client initialized and tested.
- **RAG Layer**: Not implemented yet.

## 3. Current Technology Stack
- **Frontend**: React, TypeScript, Vite
- **Backend**: Python 3.11, FastAPI, Pydantic, pydantic-settings
- **Computer Vision**: OpenCV, Pillow, NumPy, Ultralytics YOLOv8-seg
- **Database**: Supabase Python client

## 4. Current Implementation Status
- **Overall Status**: In Progress
- **Frontend**: Working (Milestones 1–3 completed; automatically displays YOLO segmentation results after processing)
- **Backend**: Working (Milestones 1–3 completed and runtime verified)
- **Database/Supabase**: Initialized but credentials not provided in `.env`
- **Image Pipeline**: Completed (Quality Check + Preprocessing)
- **AI Pipeline**: Completed for the current prototype model; configurable local checkpoint, CPU inference, masks, overlays, and multiple detections are verified.
- **RAG System**: Not Started

## 5. Current Milestone
**MILESTONE 3 — AI INFERENCE — COMPLETED AND RUNTIME VERIFIED**
- **Objective**: Run a configurable local YOLOv8-seg checkpoint on the existing processed image and display its result.
- **Work Completed**:
  - Configurable `MODEL_PATH` (default `models/best.pt`), confidence threshold, and image size.
  - `POST /api/run-inference` consumes only the processed image URL from `/api/process-image`, loads a cached Ultralytics YOLOv8-seg model, and explicitly uses CPU inference.
  - Response includes detected class, confidence, xyxy box, segmentation polygon, mask URL, and overlay URL.
  - Missing weights return explicit `model_not_available` with no fabricated prediction.
  - The frontend automatically chains process → inference and displays the overlay/detection table or unavailable-model message.
  - Python 3.11 virtual environment and runtime dependencies are working.
  - Runtime flow was verified with a real YOLOv8-seg crack-segmentation checkpoint, including multiple crack detections, masks, and overlay output.
  - Current model selected for continued local development: YOLOv8m with `{0: "crack"}`.
- **Work Remaining**: Begin Milestone 4: computer-vision post-processing and damage measurement.
- **Limitations**: The YOLOv8m checkpoint is only a prototype/integration model, not a final heritage-trained AWIS-HM model. Heritage-specific fine-tuning and formal evaluation are still pending; no final accuracy metrics are claimed.

## 6. What Was Built
- **Backend**:
  - `backend/main.py`: Updated to include process router and mount `/uploads` for static files.
  - `backend/api/process.py`: New API route (`POST /api/process-image`).
  - `backend/services/process_service.py`: Image preprocessing pipeline using OpenCV.
  - `backend/schemas/process.py`: Pydantic schemas for process responses and metadata.
  - `backend/api/inference.py`: `POST /api/run-inference`.
  - `backend/services/inference_service.py`: Cached CPU YOLO loading, inference, overlay/mask output, and processed-image URL validation.
  - `backend/schemas/inference.py`: Inference API schemas.
- **Frontend**:
  - `frontend/src/App.tsx`: Updated to use the new process API and display before/after previews and metadata.
  - `frontend/src/types.ts`: Updated to include `ProcessResponse` and `ProcessMetadata` types.
  - `frontend/src/vite-env.d.ts`: Vite type declaration required for TypeScript CSS imports.
- **Tests**:
  - `tests/test_process_api.py`: FastAPI test client suite for the image processing endpoint.
  - `tests/test_inference_api.py`: Missing-checkpoint and accepted-input-path behavior.

## 7. Important Decisions
- **Hardware Constraints**: Local development must work without a GPU (target: AMD Ryzen 5 CPU). Local runtime must support CPU inference.
- **Model Training**: Heavy model training is done offline in Google Colab; the laptop only uses the trained `.pt` checkpoint for inference.
- **Current Model Choice**: YOLOv8m crack segmentation is used for continued local CPU development because it is lighter than YOLOv8x. YOLOv8x appeared stronger on one separate test image, but that is not a formal comparison or accuracy result.
- **Database**: Hosted Supabase is used instead of a local PostgreSQL server.
- **RAG / AI APIs**: No local LLMs. Uses configurable external APIs for embeddings and LLM generation. Credentials must be environment variables.
- **UI Design System**: Must use a professional heritage-engineering visual theme (dark charcoal base, warm stone/earth accents, terracotta accents). Emojis are strictly prohibited.
- **CORS Setup**: Used `get_allowed_origins()` to handle `.env` comma-separated values correctly for `CORSMiddleware`.
- **Static Image Proxy**: Vite proxies `/uploads` to the FastAPI server because process responses intentionally return backend-relative static URLs.
- **Quality Gate Design**: Every metric uses two tiers (FAIL = genuinely unusable, WARNING = imperfect but usable). No preprocessing is applied in the quality gate — altering pixel data could create or remove crack features. All thresholds are provisional (not scientifically validated) and fully configurable via env vars.
- **Preprocessing Restrictions**: Preprocessing is strictly CPU-friendly (e.g., OpenCV basic filters) and entirely skipped if an image FAILS the quality gate. Applied operations are returned in a metadata array to aid transparency.
- **Inference Input**: YOLO only accepts a local `/uploads/...` image returned by the processing route. It does not repeat quality checking or preprocessing.
- **Model Honesty**: The absence of a checkpoint is a visible `model_not_available` state. An empty detection list means a model actually ran and detected nothing.
- **Prototype Behaviour**: The generic crack prototype can detect multiple cracks in one image, but may produce false positives on non-real/artificial crack imagery. This is expected and must not be presented as final heritage-model performance.

## 8. Environment & Run Instructions
- **Frontend**:
  - `cd frontend`
  - `npm install`
  - `npm run dev` (Runs on `http://localhost:5173`)
- **Backend**:
  - Create/activate Python 3.11 virtual environment: `py -3.11 -m venv .venv` then `.\.venv\Scripts\Activate.ps1`.
  - Install dependencies: `python -m pip install -r requirements.txt`
  - Run server: `python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload`
- **Environment Variables**:
  - Copy `.env.example` to `.env` and populate Supabase credentials.
  - Set `MODEL_PATH=models/best.pt` (must be a compatible YOLOv8 segmentation checkpoint), `YOLO_CONFIDENCE_THRESHOLD=0.25`, and `YOLO_IMAGE_SIZE=640` as needed.

## 9. Testing Status
- **Milestones**: Milestone 1 (Foundation), Milestone 2 (Image Pipeline), and Milestone 3 (AI Inference) are completed.
- **Tests Implemented**: `tests/test_quality_regression.py` (6 tests), `tests/test_process_api.py` (7 tests), and `tests/test_inference_api.py`.
- **Tests Passed**: 13 / 13.
- **Tests Failed**: 0.
- **Milestone 3 static check (2026-10-07)**: `npm run build` passed.
- **Milestone 3 runtime check**: Completed with Python 3.11 virtual environment and a real YOLOv8-seg crack-segmentation checkpoint. The verified flow is upload → quality check → preprocessing → CPU inference → visible segmentation overlay/detection table.
- **Processing Regression Test Results (2026-10-06)**:
  - Valid wall-like image -> PASSED (status: pass, preprocessed)
  - Low-light image -> PASSED (status: fail, skipped)
  - Blurry image -> PASSED (status: fail, skipped)
  - Corrupt image -> PASSED (status: fail, skipped)
  - Unsupported file -> PASSED (status 415)
  - Very small image -> PASSED (status: fail, skipped)
  - Low-contrast image -> PASSED (status: pass/warning, preprocessed)

## 10. Known Problems / Blockers
- No active implementation blocker for the completed prototype inference flow.
- Final heritage-specific model fine-tuning/evaluation is pending. The current local checkpoint remains a prototype and is intentionally not committed to Git.

## 10a. Resolved Issues
- **Issue**: Quality checker classified usable wall images as FAIL (2026-10-06).
  - **Root Cause**: The original quality-check service used a single-tier threshold system.
  - **Fix Applied**: Replaced single-tier thresholds with two-tier FAIL/WARNING/PASS classification.

## 11. Next Immediate Task
- Begin **MILESTONE 4 — COMPUTER VISION / DAMAGE MEASUREMENT**: add segmentation-mask post-processing, crack geometry extraction, pixel measurements, and calibrated-mm handling when suitable calibration is available. Do not add scoring, history, RAG, or reports yet.

## 12. Change Log
- **2026-10-05**: Initialized `PROJECT_CONTEXT.md` prior to starting Milestone 1.
- **2026-10-06 (AM)**: Completed MILESTONE 1. Implemented React frontend, FastAPI backend, image quality checks, and Supabase integration logic. Tested and verified local run.
- **2026-10-06 (PM)**: Fixed quality-check false-reject bug.
- **2026-10-06 (Evening)**: Completed MILESTONE 2. Implemented the conditional image preprocessing pipeline (`POST /api/process-image`). Added before/after UI and test suite for the pipeline. All tests passed.
- **2026-10-06 (Late evening)**: Fixed Milestone 2 manual UI result display. The backend returned valid `/uploads/...` URLs, but Vite did not proxy `/uploads`, so the browser received the SPA HTML fallback instead of JPEG bytes. Added the `/uploads` Vite proxy and verified the live before/after flow plus quality-fail behavior.
- **2026-10-07**: Implemented and runtime-verified Milestone 3 with a Python 3.11 virtual environment and a real YOLOv8-seg crack checkpoint. CPU inference returns multiple detections where present, masks/polygons, and overlays. Continued development uses YOLOv8m `{0: "crack"}` as a lighter prototype model; heritage-specific fine-tuning/evaluation remains pending.
