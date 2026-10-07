# AWIS-HM

## AI-Based Wall Inspection System for Heritage Masonry

AWIS-HM is a local web application that assists inspection of **visible surface damage** in heritage masonry images. It combines image-quality control, conditional preprocessing, and YOLOv8 segmentation to present crack detections for engineering or conservation review.

It is an inspection-assistance and decision-support tool. It does not certify structural safety and cannot detect internal, hidden, subsurface, or other non-visible damage.

## Goal

Build a practical image-to-inspection workflow for heritage masonry that can later support damage measurement, condition assessment, inspection history, and evidence-based maintenance guidance.

## Current End-to-End Flow

```text
Upload image
  → Quality gate (PASS / WARNING / FAIL)
  → Conditional preprocessing
  → YOLOv8-seg CPU inference
  → Mask post-processing
  → Pixel measurements
  → Visible surface condition assessment
  → DOCX / PDF / PNG inspection report
```

A FAIL result stops preprocessing and inference. For usable images, the frontend automatically submits the processed image to inference and displays detected class, confidence, bounding box, segmentation mask, and overlay.

## Implemented Capabilities

- JPG and PNG upload with validation
- Quality checks for blur, brightness, contrast, and resolution
- PASS / WARNING / FAIL guidance; FAIL images do not proceed
- Conditional resizing, denoising, brightness adjustment, CLAHE, and sharpening
- FastAPI endpoint `POST /api/run-inference`
- Configurable local YOLOv8-seg checkpoint via `MODEL_PATH`
- CPU inference, bounding boxes, confidence values, segmentation polygons/masks, and overlays
- Multiple crack detections per image
- Conservative mask cleanup and pixel-only crack length, width, area, maximum width, and orientation measurements
- Rule-based Visible Surface Condition Assessment with Mild / Moderate / Severe categories
- Bounded 0-10 condition score where higher scores indicate better visible condition
- Automated reports generated from live inspection data in DOCX, PDF, and PNG formats
- Frontend visualization of processed images and inference results
- Fixed header/footer layout, centered workflow/processing views, and constrained inspection image sizes

Physical calibration and physical-unit conversion are implemented separately but deferred. They are not invoked by the live workflow, displayed in the UI, or included in reports.

## Current Model

The current local prototype is a YOLOv8m crack-segmentation checkpoint with one class:

```text
{0: "crack"}
```

Place the checkpoint at `models/best.pt` or set `MODEL_PATH` to its local path. Model weights are intentionally ignored by Git and must be supplied locally.

This is an integration/prototype model, **not** the final AWIS-HM heritage-trained model. It has no final project accuracy claim. YOLOv8x was also tried separately and appeared stronger on one test image, but development continues with YOLOv8m because it is more suitable for local CPU work. Heritage-masonry fine-tuning and formal evaluation remain pending.

## Technology Stack

- Frontend: React, TypeScript, Vite
- Backend: Python 3.11, FastAPI, Pydantic
- Vision: OpenCV, NumPy, Ultralytics YOLOv8-seg, PyTorch
- Storage: local `uploads/` directory during the prototype stage
- Planned persistence: Supabase

## Local Setup

Requirements: Python 3.11, Node.js, and npm.

Create and activate a Python virtual environment from the project root:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Copy `.env.example` to `.env` and configure `MODEL_PATH` if the checkpoint is not at `models/best.pt`.

Start the backend:

```powershell
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Start the frontend in a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The Vite development server proxies `/api` and `/uploads` to FastAPI on port 8000.

## Key Endpoints

- `GET /api/health` — backend status
- `POST /api/quality-check` — quality assessment only
- `POST /api/process-image` — quality gate and conditional preprocessing
- `POST /api/run-inference` — YOLOv8-seg on an existing processed image
- `POST /api/generate-report` — generate DOCX, PDF, and PNG reports from the current pixel-based inspection result
- `GET /api/docs` — interactive API documentation

## Planned Modules

- Physical calibration and physical-unit conversion (implemented but deferred)
- Supabase-backed inspection history
- RAG decision support and LLM-based maintenance reports
- Heritage-specific model fine-tuning and evaluation

## Scope and Limitations

AWIS-HM evaluates only visible surface features represented in the submitted image. Image quality, lighting, viewpoint, wall material, and the current prototype model can affect results. Generic crack models may produce false positives on non-real or artificial crack imagery. All consequential conservation, maintenance, or safety decisions require qualified professional review.
