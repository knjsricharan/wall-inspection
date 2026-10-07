# PROJECT_CONTEXT

## 1. Project Summary
AWIS-HM (AI-Based Wall Inspection System for Heritage Masonry) is a web-based end-to-end system that accepts a smartphone image of a heritage masonry wall and produces a surface condition inspection result. It uses YOLOv8-seg for damage detection and segmentation, computes crack measurements (length, width, area), scores the condition, and features a RAG (Retrieval-Augmented Generation) decision-support layer to generate evidence-backed inspection reports. It evaluates visible surface damage only.

## 2. Current Architecture
- **Frontend**: React application running on the user's laptop. (Running via Vite dev server)
- **Backend Orchestrator**: FastAPI handling API requests and workflow. (Running via Uvicorn)
- **Image Pipeline**: Quality check and conditional preprocessing implemented using OpenCV.
- **AI Inference**: YOLOv8-seg CPU inference is implemented and runtime verified with a real local crack-segmentation checkpoint.
- **Post-Processing & Measurement**: Implemented for YOLO segmentation masks with conservative cleanup and uncalibrated pixel measurements.
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
**CURRENT PHASE — PIXEL CONDITION ASSESSMENT AND AUTOMATED REPORT — IMPLEMENTED / LIVE**
- **Objective**: Clean YOLO segmentation masks conservatively and calculate uncalibrated pixel measurements for crack detections.
- **Work Completed**:
  - Added a separate mask post-processing service for binary mask validation, small-region removal, and small-gap closing.
  - Added a separate measurement service for area, skeleton length, distance-transform width, maximum width, and PCA-based orientation.
  - Extended `POST /api/run-inference` so the existing inference flow now performs post-processing and measurement after YOLO segmentation.
  - Preserved existing response fields: detection class, confidence, bounding box, raw mask URL, polygon, and overlay URL.
  - Added per-detection measurement fields and a response-level measurement summary.
  - Added cleaned mask files and a measurement overlay without replacing the existing detection overlay.
  - Updated the frontend Results page to show uncalibrated pixel measurements and cleaned-mask links only when returned by the backend.
  - Added synthetic-mask unit tests and an inference API regression test using a fake deterministic model result.
- **Work Remaining**: Runtime verification with the local YOLO checkpoint after Python 3.11 is restored. Begin Milestone 5 only after measurement tests pass in the repaired environment.
- **Limitations**: Measurements are uncalibrated pixel values only. Physical mm/mm² calibration is pending. The YOLOv8m checkpoint remains a prototype/integration model, not a final heritage-trained AWIS-HM model; no final accuracy metrics are claimed.

## 6. What Was Built
- **Backend**:
  - `backend/main.py`: Updated to include process router and mount `/uploads` for static files.
  - `backend/api/process.py`: New API route (`POST /api/process-image`).
  - `backend/services/process_service.py`: Image preprocessing pipeline using OpenCV.
  - `backend/schemas/process.py`: Pydantic schemas for process responses and metadata.
  - `backend/api/inference.py`: `POST /api/run-inference`.
  - `backend/services/inference_service.py`: Cached CPU YOLO loading, inference, overlay/mask output, cleaned-mask output, measurement overlay output, pixel measurement integration, and processed-image URL validation.
  - `backend/services/postprocess_service.py`: Conservative binary segmentation mask cleanup.
  - `backend/services/measurement_service.py`: Uncalibrated crack area, skeleton length, distance-transform width, maximum width, and orientation measurement.
  - `backend/schemas/inference.py`: Inference and measurement API schemas.
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
- **Measurement Units**: The live workflow uses pixel measurements only. Physical calibration and conversion remain implemented but deferred and are not invoked by normal inference, shown in the UI, or included in reports.
- **Calibration**: `backend/services/calibration_service.py` is retained for future use only. The physical calibration / physical-unit conversion component has already been implemented separately. It is intentionally excluded from the live UI and current inspection workflow because reliable physical scale cannot be guaranteed for arbitrary uploaded wall images. The live system therefore uses uncalibrated pixel-level measurements.
- **Condition Assessment**: `backend/services/condition_service.py` is live and uses explainable, centralized project-defined prototype thresholds over pixel width, area, length, count, and confidence. Its condition score is bounded 0-10 with 10 representing best visible surface condition and 0 representing greatest visible damage; higher score means better condition. Categories are Mild, Moderate, and Severe. It reports visible surface condition only and is not a structural-safety standard.
- **Reports**: `backend/services/report_service.py` generates reports only from the current live inspection payload in DOCX, PDF, and PNG formats. Reports contain pixel findings, condition assessment, limitations, and scope disclaimer; no physical calibration, RAG, or LLM content.
- **Post-Processing Philosophy**: Mask cleanup is intentionally conservative. Small isolated regions may be removed by configurable threshold, but detections must not be hidden because they look unusual.

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
  - Optional post-processing settings: `MASK_MIN_REGION_AREA_PX`, `MASK_CLOSING_KERNEL_SIZE`, and `MASK_CLOSING_ITERATIONS`.
  - Calibration settings remain available for deferred future use but are not part of the live workflow.
  - Optional condition settings: `CONDITION_*_MM`, `CONDITION_*_MM2`, `CONDITION_*_PX`, `CONDITION_*_PX2`, confidence thresholds, and `CONDITION_UNCALIBRATED_SUPPORTED`.

## 9. Testing Status
- **Milestones**: Milestones 1-4 are implemented. Current phase modules are live pixel condition assessment and automated inspection reporting; physical calibration is implemented but deferred.
- **Tests Implemented**: Existing quality/process/inference suites, `tests/test_measurement_services.py`, `tests/test_calibration_condition.py`, and `tests/test_report_service.py`.
- **Latest Verification (2026-10-07)**:
  - `npm run build` passed.
  - `rg "AWIS-HM" frontend` returned no matches, confirming no new forbidden frontend acronym text.
  - `python -m compileall backend tests` passed using the bundled Python for syntax checks.
  - Full suite completion was not verified because the process API suite exceeded the available verification window. The configured Python 3.11 environment now runs pytest; the bundled Python still lacks the project's `pydantic-settings` dependency for report smoke execution.
  - Focused condition, measurement, calibration, and report tests: 18 passed.
  - Quality regression tests: 6 passed.
  - The process API suite exceeded the available verification window and was stopped without an application failure result.
- **Previous Tests Passed**: 13 / 13 before Milestone 4 changes.
- **Tests Failed**: No application test failures observed in this run; full pytest execution was blocked by the local Python runtime mismatch.
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
- Local Python verification blocker: `.venv` was created from `C:\Users\srich\AppData\Local\Python\pythoncore-3.11-64\python.exe`, but that interpreter is no longer available. Recreate the Python 3.11 environment and reinstall `requirements.txt` before running the full backend tests.
- Final heritage-specific model fine-tuning/evaluation is pending. The current local checkpoint remains a prototype and is intentionally not committed to Git.
- The physical calibration module may not be available in every OpenCV build; it remains isolated and deferred. Physical measurements depend on a valid image-specific scale reference.

## 10a. Resolved Issues
- **Issue**: Quality checker classified usable wall images as FAIL (2026-10-06).
  - **Root Cause**: The original quality-check service used a single-tier threshold system.
  - **Fix Applied**: Replaced single-tier thresholds with two-tier FAIL/WARNING/PASS classification.

## 11. Next Immediate Task
- Repair/recreate the Python 3.11 virtual environment, run all tests, render and inspect generated DOCX/PDF/PNG artifacts, and manually verify the live pixel workflow plus downloads. Physical calibration remains deferred. Do not add RAG, LLM recommendations, history, Supabase persistence, comparison, or structural safety evaluation.

## 12. Change Log
- **2026-10-05**: Initialized `PROJECT_CONTEXT.md` prior to starting Milestone 1.
- **2026-10-06 (AM)**: Completed MILESTONE 1. Implemented React frontend, FastAPI backend, image quality checks, and Supabase integration logic. Tested and verified local run.
- **2026-10-06 (PM)**: Fixed quality-check false-reject bug.
- **2026-10-06 (Evening)**: Completed MILESTONE 2. Implemented the conditional image preprocessing pipeline (`POST /api/process-image`). Added before/after UI and test suite for the pipeline. All tests passed.
- **2026-10-06 (Late evening)**: Fixed Milestone 2 manual UI result display. The backend returned valid `/uploads/...` URLs, but Vite did not proxy `/uploads`, so the browser received the SPA HTML fallback instead of JPEG bytes. Added the `/uploads` Vite proxy and verified the live before/after flow plus quality-fail behavior.
- **2026-10-07**: Implemented and runtime-verified Milestone 3 with a Python 3.11 virtual environment and a real YOLOv8-seg crack checkpoint. CPU inference returns multiple detections where present, masks/polygons, and overlays. Continued development uses YOLOv8m `{0: "crack"}` as a lighter prototype model; heritage-specific fine-tuning/evaluation remains pending.
- **2026-10-07**: Implemented Milestone 4 mask post-processing and pixel measurement. Added conservative cleaned masks, area, skeleton length, representative width, maximum width, orientation, measurement summary, cleaned-mask/measurement overlays, frontend result display, and synthetic-mask tests. Frontend build and syntax checks passed; full pytest run is pending Python 3.11 environment repair.
- **2026-10-07**: Implemented MILESTONE 5 physical measurement calibration and visible-surface condition assessment. Added per-image ArUco calibration with safe failure, additive mm/cm and mm²/cm² conversions, calibration overlay, configurable calibrated/pixel prototype thresholds, Mild/Moderate/Severe assessment, frontend calibration/measurement/assessment sections, and focused tests. Syntax compilation and frontend build passed; full pytest and live marker/manual flows remain pending Python runtime repair and suitable test images.
- **2026-10-07**: Activated the current phase's live pixel-only condition assessment and automated report generation. Normal inference no longer invokes calibration; the Results page shows pixel mode, condition status, and report downloads. Added DOCX, PDF, and PNG report generation from actual live payloads, API endpoint, frontend controls, and report tests. Backend syntax and frontend build passed; full runtime tests and visual artifact QA remain pending environment repair.
- **2026-10-07**: Fixed backend startup when report-only dependencies are absent. DOCX/PDF/PNG libraries are now imported lazily during report generation, `python-docx` and `reportlab` are listed in `requirements.txt`, and the report endpoint returns a controlled error instead of preventing Uvicorn startup. `import backend.main` verified successfully.
- **2026-10-07**: Fixed a live condition-response validation bug caused by positional dataclass construction after adding `measurement_mode`. Condition assessment results now use named fields and correctly return pixel mode plus preliminary status.
- **2026-10-07**: Corrected condition-score semantics so the score is an inverse damage score: higher scores indicate better visible condition, lower scores indicate greater visible damage, and category cutoffs are configurable. Added monotonicity and bounded-score tests. Centered the workflow stepper and processing page, moderately reduced dashboard hero spacing, and preserved compact image limits in the frontend.
