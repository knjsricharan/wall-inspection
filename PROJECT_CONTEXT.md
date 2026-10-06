# PROJECT_CONTEXT

## 1. Project Summary
AWIS-HM (AI-Based Wall Inspection System for Heritage Masonry) is a web-based end-to-end system that accepts a smartphone image of a heritage masonry wall and produces a surface condition inspection result. It uses YOLOv8-seg for damage detection and segmentation, computes crack measurements (length, width, area), scores the condition, and features a RAG (Retrieval-Augmented Generation) decision-support layer to generate evidence-backed inspection reports. It evaluates visible surface damage only.

## 2. Current Architecture
- **Frontend**: React application running on the user's laptop. (Running via Vite dev server)
- **Backend Orchestrator**: FastAPI handling API requests and workflow. (Running via Uvicorn)
- **Image Pipeline**: Quality check and conditional preprocessing implemented using OpenCV.
- **AI Inference**: Not implemented yet.
- **Post-Processing & Measurement**: Not implemented yet.
- **Database**: Supabase client initialized and tested.
- **RAG Layer**: Not implemented yet.

## 3. Current Technology Stack
- **Frontend**: React, TypeScript, Vite
- **Backend**: Python 3.11, FastAPI, Pydantic, pydantic-settings
- **Computer Vision**: OpenCV, Pillow, NumPy
- **Database**: Supabase Python client

## 4. Current Implementation Status
- **Overall Status**: In Progress
- **Frontend**: Working (Milestone 2 completed; upload proxy fix verified)
- **Backend**: Working (Milestone 2 completed)
- **Database/Supabase**: Initialized but credentials not provided in `.env`
- **Image Pipeline**: Completed (Quality Check + Preprocessing)
- **AI Pipeline**: Not Started
- **RAG System**: Not Started

## 5. Current Milestone
**MILESTONE 2 — IMAGE PIPELINE**
- **Objective**: Implement the image preprocessing/enhancement pipeline conditionally after quality checks.
- **Work Completed**:
  - Image decoding and validation logic.
  - Integration with existing two-tier FAIL/WARNING/PASS quality system.
  - Conditional preprocessing (skipped if quality FAILS).
  - Preprocessing operations: Aspect-ratio preserving resize (max 1024), mild denoising (Gaussian), brightness correction (conditional L-channel), CLAHE contrast enhancement, mild sharpening.
  - New API endpoint `POST /api/process-image`.
  - Frontend UI updated to show Original vs Processed images and applied operations metadata.
  - Test suite with 7 scenarios (valid, low-light, blurry, corrupt, unsupported, very small, low-contrast).
- **Work Remaining**: None for Milestone 2.
- **Limitations**: No real heritage images used; testing relies exclusively on synthetic fixtures.

## 6. What Was Built
- **Backend**:
  - `backend/main.py`: Updated to include process router and mount `/uploads` for static files.
  - `backend/api/process.py`: New API route (`POST /api/process-image`).
  - `backend/services/process_service.py`: Image preprocessing pipeline using OpenCV.
  - `backend/schemas/process.py`: Pydantic schemas for process responses and metadata.
- **Frontend**:
  - `frontend/src/App.tsx`: Updated to use the new process API and display before/after previews and metadata.
  - `frontend/src/types.ts`: Updated to include `ProcessResponse` and `ProcessMetadata` types.
- **Tests**:
  - `tests/test_process_api.py`: FastAPI test client suite for the image processing endpoint.

## 7. Important Decisions
- **Hardware Constraints**: Local development must work without a GPU (target: AMD Ryzen 5 CPU). Local runtime must support CPU inference.
- **Model Training**: Heavy model training is done offline in Google Colab; the laptop only uses the trained `.pt` checkpoint for inference.
- **Database**: Hosted Supabase is used instead of a local PostgreSQL server.
- **RAG / AI APIs**: No local LLMs. Uses configurable external APIs for embeddings and LLM generation. Credentials must be environment variables.
- **UI Design System**: Must use a professional heritage-engineering visual theme (dark charcoal base, warm stone/earth accents, terracotta accents). Emojis are strictly prohibited.
- **CORS Setup**: Used `get_allowed_origins()` to handle `.env` comma-separated values correctly for `CORSMiddleware`.
- **Static Image Proxy**: Vite proxies `/uploads` to the FastAPI server because process responses intentionally return backend-relative static URLs.
- **Quality Gate Design**: Every metric uses two tiers (FAIL = genuinely unusable, WARNING = imperfect but usable). No preprocessing is applied in the quality gate — altering pixel data could create or remove crack features. All thresholds are provisional (not scientifically validated) and fully configurable via env vars.
- **Preprocessing Restrictions**: Preprocessing is strictly CPU-friendly (e.g., OpenCV basic filters) and entirely skipped if an image FAILS the quality gate. Applied operations are returned in a metadata array to aid transparency.

## 8. Environment & Run Instructions
- **Frontend**:
  - `cd frontend`
  - `npm install`
  - `npm run dev` (Runs on `http://localhost:5173`)
- **Backend**:
  - Install dependencies: `pip install fastapi uvicorn python-multipart opencv-python-headless pillow numpy supabase python-dotenv pydantic-settings httpx`
  - Run server: `python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload`
- **Environment Variables**:
  - Copy `.env.example` to `.env` and populate Supabase credentials.

## 9. Testing Status
- **Tests Implemented**: `tests/test_quality_regression.py` (6 tests), `tests/test_process_api.py` (7 tests).
- **Tests Passed**: 13 / 13.
- **Tests Failed**: 0.
- **Processing Regression Test Results (2026-10-06)**:
  - Valid wall-like image -> PASSED (status: pass, preprocessed)
  - Low-light image -> PASSED (status: fail, skipped)
  - Blurry image -> PASSED (status: fail, skipped)
  - Corrupt image -> PASSED (status: fail, skipped)
  - Unsupported file -> PASSED (status 415)
  - Very small image -> PASSED (status: fail, skipped)
  - Low-contrast image -> PASSED (status: pass/warning, preprocessed)

## 10. Known Problems / Blockers
- None at this time.

## 10a. Resolved Issues
- **Issue**: Quality checker classified usable wall images as FAIL (2026-10-06).
  - **Root Cause**: The original quality-check service used a single-tier threshold system.
  - **Fix Applied**: Replaced single-tier thresholds with two-tier FAIL/WARNING/PASS classification.

## 11. Next Immediate Task
- Proceed to **MILESTONE 3 — AI INFERENCE**: Add YOLOv8-seg integration, configurable checkpoint loading, CPU inference support, and segmentation visualization over the processed images.

## 12. Change Log
- **2026-10-05**: Initialized `PROJECT_CONTEXT.md` prior to starting Milestone 1.
- **2026-10-06 (AM)**: Completed MILESTONE 1. Implemented React frontend, FastAPI backend, image quality checks, and Supabase integration logic. Tested and verified local run.
- **2026-10-06 (PM)**: Fixed quality-check false-reject bug.
- **2026-10-06 (Evening)**: Completed MILESTONE 2. Implemented the conditional image preprocessing pipeline (`POST /api/process-image`). Added before/after UI and test suite for the pipeline. All tests passed.
- **2026-10-06 (Late evening)**: Fixed Milestone 2 manual UI result display. The backend returned valid `/uploads/...` URLs, but Vite did not proxy `/uploads`, so the browser received the SPA HTML fallback instead of JPEG bytes. Added the `/uploads` Vite proxy and verified the live before/after flow plus quality-fail behavior.
