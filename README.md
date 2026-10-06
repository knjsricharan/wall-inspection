# AWIS-HM

## AI-Based Wall Inspection System for Heritage Masonry

AWIS-HM is a web-based inspection system for evaluating visible surface conditions in heritage masonry images. The project is designed to support engineering review by combining image-quality assessment, conditional image preprocessing, and future computer-vision-based damage analysis.

The system does not replace a qualified structural engineer, conservation specialist, or formal building inspection. It assesses visible image content only and cannot determine hidden, internal, or subsurface damage.

## Current Status

The project is currently at **Milestone 2 — Image Pipeline**.

Implemented:

- React and TypeScript frontend
- FastAPI backend
- JPG and PNG image upload
- Image validation and quality checks
- PASS, WARNING, and FAIL quality classification
- Conditional preprocessing for acceptable images
- Original and processed image display
- Local storage of uploaded and processed images
- Automated quality and process API tests

YOLO segmentation, damage measurement, condition scoring, database history, and RAG-based decision support are planned for later milestones and are not yet implemented.

## Workflow

```text
Upload Image
    |
Quality Check
    |
PASS or WARNING --------------> FAIL
    |                              |
Image Preprocessing          Clear Failure Guidance
    |
Processed Image
    |
Original and Processed Image Display
```

Images that fail the quality gate are not preprocessed. This preserves the quality-control boundary and ensures that unsuitable images are reported clearly to the user.

## Technology Stack

- Frontend: React, TypeScript, Vite
- Backend: Python, FastAPI, Pydantic
- Image processing: OpenCV, Pillow, NumPy
- Storage: Local `uploads/` directory during the current development stage
- Optional database integration: Supabase configuration is supported but not required for Milestone 2

## Project Structure

```text
backend/
  api/                  FastAPI route handlers
  services/             Quality checking and preprocessing services
  schemas/              API response schemas
  core/                 Application configuration
  main.py               FastAPI application entry point

frontend/
  src/                  React application source
  vite.config.ts        Development server and API/static-file proxy

tests/
  fixtures/             Sample wall images for testing
  test_quality_regression.py
  test_process_api.py

uploads/                Locally stored original and processed images
```

## Requirements

- Python 3.11 or a compatible Python version
- Node.js and npm
- The Python dependencies listed in the project setup instructions

## Running the Application

Start the backend from the project root:

```powershell
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Start the frontend in a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the application at:

```text
http://localhost:5173
```

The frontend proxies API requests and uploaded-image requests to the FastAPI server on port 8000.

## API Endpoints

- `GET /api/health` — backend health and configuration status
- `POST /api/quality-check` — evaluate image quality without preprocessing
- `POST /api/process-image` — run the quality gate and conditionally preprocess the image
- `GET /api/docs` — interactive FastAPI documentation
- `/uploads/...` — locally served original and processed image files

The process endpoint expects a multipart form field named `image`.

## Testing

Run the existing tests from the project root:

```powershell
python -m pytest tests/test_quality_regression.py tests/test_process_api.py
```

The test fixtures include sharp, blurry, dark, corrupt, low-contrast, and wall-crack images. The expected behavior is that failed images stop at the quality gate and do not enter preprocessing.

## Quality and Ethical Use

Quality thresholds are configurable project-defined values. They are provisional engineering settings and must not be treated as scientifically validated safety limits.

The system should be used to support inspection and documentation, not to issue autonomous structural-safety certifications. Results may be affected by lighting, blur, camera angle, image resolution, wall material, and dataset limitations. Any consequential maintenance or safety decision must be reviewed by an appropriately qualified professional.

The project must not fabricate detections, measurements, model accuracy, citations, or inspection results. Features that are not implemented must be clearly identified as planned work.

## Roadmap

1. Milestone 1 — Foundation
2. Milestone 2 — Image Pipeline (current)
3. Milestone 3 — YOLOv8 segmentation inference
4. Milestone 4 — Damage measurement
5. Milestone 5 — Condition assessment
6. Milestone 6 — Database and inspection history
7. Milestone 7 — Retrieval-Augmented Generation decision support
8. Milestone 8 — Full end-to-end integration
9. Milestone 9 — Testing and review preparation

## License and Research Use

No production or open-source license has been declared yet. Until licensing is clarified, treat this repository as a development and research project and do not redistribute it as a production inspection tool without appropriate review and permission.
