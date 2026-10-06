# AWIS-HM — AI-Based Wall Inspection System for Heritage Masonry

## 1. PROJECT IDENTITY

Project:
AI-Based Wall Inspection System for Heritage Masonry

Short Name:
AWIS-HM

Type:
Web-based end-to-end heritage wall inspection and decision-support system.

Primary Reference:
`Final_Draft_Rewritten.docx`

The final draft is the primary source of truth for:
- project scope
- research-supported methods
- proposed architecture
- training methodology
- limitations
- RAG concept
- expected workflow

Do not invent research results.
Do not present results from cited papers as results achieved by this project.

---

# 2. PROJECT GOAL

Build a working end-to-end system that accepts a smartphone image of a heritage masonry wall and produces an inspection result.

Core workflow:

Image Upload
→ Image Quality Check
→ Preprocessing
→ YOLOv8 Segmentation
→ Post-Processing
→ Crack/Damage Measurement
→ Condition Assessment
→ Inspection History
→ RAG Decision Support
→ Evidence-Based Report

The system assesses visible surface damage only.

It must NOT claim to:
- detect internal structural damage
- detect hidden/subsurface damage
- replace professional structural assessment

---

# 3. SYSTEM ARCHITECTURE

## Runtime

The user's laptop runs the application.

Laptop:

React
↓
FastAPI
↓
Image Processing
↓
YOLOv8-seg + trained checkpoint
↓
Measurement
↓
Condition Assessment
↓
Supabase
↓
RAG orchestration
↓
External APIs
↓
Report

External services:

Google Colab
→ model training
→ trained `.pt` checkpoint
→ checkpoint downloaded to laptop

Supabase
→ PostgreSQL
→ pgvector
→ inspection history
→ RAG knowledge vectors

External APIs
→ embeddings
→ LLM generation

The React frontend must never communicate directly with the ML model, database or LLM provider when unnecessary.
FastAPI acts as the main application/backend layer.

---

# 4. HARDWARE CONSTRAINT

Development laptop:

AMD Ryzen 5 3500U CPU.

Therefore:

- local development must work without a GPU
- YOLO inference must support CPU execution
- avoid unnecessary local services
- do not require a local LLM
- use external APIs for embeddings and LLM generation
- heavy model training must be performed outside the laptop
- Google Colab is the initial training environment

Initial local inference target:

- YOLOv8s-seg
- 640px input
- batch size 1
- CPU inference
- one image per inspection

YOLOv8m-seg may be evaluated later for accuracy comparison.

The model checkpoint must be replaceable without redesigning the application.

---

# 5. TRAINING AND MODEL DEPLOYMENT

Training is an offline process.

Training workflow:

Dataset
→ Annotation
→ Train/Validation/Test Split
→ YOLOv8-seg Training in Google Colab
→ Evaluation
→ `best.pt`

The trained checkpoint is then downloaded from Colab to the laptop.

Example:

`models/best.pt`

Runtime workflow:

Uploaded Image
→ Local YOLOv8 inference
→ `best.pt`
→ Detection + Segmentation

The laptop does NOT retrain the model during normal application execution.

The application should support replacing the checkpoint without changing the rest of the system.

Training should follow the final draft's research methodology, including:
- heritage-specific data
- multiple sites where possible
- suitable augmentation
- splitting before augmentation
- comparison of YOLOv8-seg model sizes
- held-out validation
- appropriate evaluation metrics

Never fabricate model accuracy.

---

# 6. TECHNOLOGY STACK

## Frontend

- React
- TypeScript or JavaScript
- responsive component-based UI

Responsibilities:
- image upload
- wall selection
- inspection progress
- result visualization
- inspection history
- report display
- report export

## Backend

- Python 3.11
- FastAPI
- Pydantic

Responsibilities:
- REST API
- input validation
- inspection workflow orchestration
- ML/CV integration
- database communication
- RAG integration
- report generation

## Computer Vision

- OpenCV
- NumPy

Responsibilities:
- image quality checks
- preprocessing
- segmentation post-processing
- crack measurement
- overlays and visualization

## Deep Learning

- PyTorch
- Ultralytics
- YOLOv8-seg

## Database

- Supabase
- PostgreSQL
- pgvector

Supabase is the hosted database/vector backend.

Do not require a local PostgreSQL server.

## External APIs

Use configurable APIs for:
- embeddings
- LLM generation

Never hard-code API keys.

## Storage

Use local storage initially for:
- original images
- processed images
- masks
- overlays
- generated reports

---

# 7. CORE MODULES

The system must have clear separation between modules.

## 7.1 Upload

Input:
- JPG/JPEG/PNG image

Responsibilities:
- file validation
- size validation
- upload handling
- associate image with wall/inspection

## 7.2 Image Quality

Check:
- blur
- exposure
- glare
- viewing angle
- image dimensions

Output:
- PASS
- WARNING
- FAIL
- metrics
- user guidance

Quality thresholds must be configurable.

Do not treat arbitrary thresholds as scientifically validated.

## 7.3 Preprocessing

Responsibilities:
- model-compatible resizing
- handling large images
- optional enhancement
- overlapping tiling where necessary
- coordinate preservation

Optional enhancement may include:
- CLAHE
- denoising
- brightness/contrast adjustment

Do not force enhancement on every image.

## 7.4 AI Inference

Input:
- preprocessed image/tile

Output:
- damage class
- confidence
- bounding box
- segmentation mask

Initial target classes:
- crack
- spalling
- vegetation

The architecture must support adding additional classes later.

## 7.5 Post-Processing

Responsibilities:
- remove small noisy regions
- close small gaps
- separate touching regions where useful
- reduce obvious false positives
- merge overlapping tile predictions

Output:
- cleaned masks

Do not hard-code a specific post-processing algorithm if a better implementation is required after testing.

## 7.6 Measurement

For crack detections calculate:
- length
- width
- area

Where calibration is available:
- report physical units such as mm and mm²

Without calibration:
- report pixel measurements
- mark them as uncalibrated

Do not invent scale values.

## 7.7 Condition Assessment

Output:
- Mild
- Moderate
- Severe

Use:
- crack measurements
- damage information
- model confidence

Scoring rules must be configurable.

Thresholds are project-defined unless independently verified through an approved standard/domain expert.

Do not present provisional thresholds as structural-safety limits.

## 7.8 Inspection History

Store:
- wall information
- inspection timestamp
- image references
- detected damage
- measurements
- condition assessment
- report metadata

Support repeated inspections of the same wall.

## 7.9 RAG

RAG is a separate decision-support layer.

It must NOT:
- detect cracks
- segment images
- calculate measurements
- change condition scores

It only uses completed inspection findings to retrieve evidence and generate grounded guidance.

## 7.10 Report

Combine:
- inspection information
- detected damage
- measurements
- condition assessment
- overlay
- RAG guidance
- citations
- limitations/disclaimer

---

# 8. DATABASE

Use Supabase PostgreSQL + pgvector.

Minimum logical entities:

## Wall

- wall_id
- wall_name
- site_name
- location
- material_type
- created_at

## Inspection

- inspection_id
- wall_id
- timestamp
- image references
- quality status
- condition score
- summary metrics

## Detection

- detection_id
- inspection_id
- damage class
- confidence
- bounding box
- mask reference/data
- measurements
- measurement unit

## Report

- report_id
- inspection_id
- report content
- citations
- expert-review status
- created_at

## RAG Knowledge

- chunk_id
- source document
- source type
- page/section reference
- chunk text
- embedding

Use UUIDs, foreign keys, timestamps and migrations.

Database credentials must come from environment variables.

---

# 9. RAG ARCHITECTURE

Knowledge sources must be approved technical material such as:
- heritage conservation guidelines
- masonry standards
- repair/maintenance documentation
- selected research papers
- supervisor-approved sources

Do not use arbitrary web content as authoritative evidence.

RAG flow:

Approved Document
→ Text Extraction
→ Chunking
→ Embedding API
→ Supabase pgvector

Inspection Findings
→ Retrieval Query
→ Embedding API
→ pgvector similarity search
→ Relevant passages
→ LLM API
→ Citation Validation
→ Report

Initial retrieval target:
- top 5 relevant passages

Keep provider and model configurable.

Example environment configuration:

EMBEDDING_API_KEY=
EMBEDDING_API_URL=
EMBEDDING_MODEL=

LLM_API_KEY=
LLM_API_URL=
LLM_MODEL=
LLM_TEMPERATURE=

Never hard-code credentials.

## Grounding Rules

The LLM must:
- use retrieved/approved evidence
- avoid unsupported technical claims
- avoid inventing standards
- avoid inventing citations
- clearly state when evidence is insufficient
- never claim internal structural damage is absent
- never modify actual inspection measurements or scores

Each generated recommendation should include a valid source/chunk citation.

If citation validation fails:
- flag the report
- set `expert_review_required = true`

---

# 10. FRONTEND USER FLOW

Dashboard
→ Select/Create Wall
→ Upload Image
→ Quality Check
→ Processing
→ Inspection Result
→ RAG Report
→ Save/History
→ Compare Previous Inspections

Required screens:

## Dashboard
- recent inspections
- recent walls
- start inspection

## New Inspection
- wall selection
- image upload
- image preview
- start inspection

## Processing
Show actual processing stages:
- upload
- quality check
- preprocessing
- AI inference
- post-processing
- measurement
- scoring
- storage
- report

Do not mark stages complete before they actually complete.

## Result
Show:
- original image
- detection/segmentation overlay
- detections
- confidence
- measurements
- condition score

## History
Show:
- inspection dates
- scores
- crack counts
- available measurements

## Comparison
Compare stored inspections for the same wall.

Do not fabricate missing data.

## Report
Clearly separate:
- CORE INSPECTION RESULTS
- AI-GENERATED DECISION SUPPORT

Include citations and disclaimer.

---

# 11. BACKEND PRINCIPLES

FastAPI is the central orchestration layer.

Use:
- REST APIs
- Pydantic validation
- structured error handling
- reusable service modules

Keep API route files thin.

Recommended logical backend areas:

backend/
├── api/
├── services/
├── cv/
├── ml/
├── measurement/
├── scoring/
├── rag/
├── database/
├── schemas/
└── core/

Exact structure may be adjusted if a better modular structure is justified.

The backend must support the main flow:

Frontend
→ FastAPI
→ Quality Check
→ Preprocessing
→ AI Inference
→ Post-Processing
→ Measurement
→ Condition Assessment
→ Supabase
→ RAG
→ Report
→ Frontend

---

# 12. DEVELOPMENT RULES

## Rule 1 — Build incrementally

Do NOT implement the entire system in one pass.

Build one working milestone at a time.

## Rule 2 — Verify everything

After each milestone:
- run the application
- run relevant tests
- verify actual output
- fix failures before moving on

## Rule 3 — No fabrication

Never fabricate:
- model predictions
- accuracy
- measurements
- test results
- citations
- database records
- research findings

Demo data must be clearly labelled as demo data.

## Rule 4 — Preserve replaceability

Keep these replaceable:
- YOLO checkpoint
- embedding provider
- LLM provider
- scoring thresholds
- quality thresholds

## Rule 5 — Prefer simple implementation

Do not introduce unnecessary frameworks or services.

## Rule 6 — Protect the hardware constraint

Do not require:
- local GPU
- local LLM
- unnecessary local database/vector services

## Rule 7 — Keep research and engineering separate

Clearly distinguish:
- literature-supported facts
- project design decisions
- provisional thresholds
- actual experimental results

## Rule 8 — Do not overbuild

The primary objective is a working end-to-end Review 2 demonstration.

Build the complete vertical slice first.
Optimize and expand afterward.

---

# 13. IMPLEMENTATION MILESTONES

## MILESTONE 1 — FOUNDATION

Build:
- React frontend
- FastAPI backend
- project structure
- environment configuration
- Supabase connection
- health check

Then verify the application runs locally.

## MILESTONE 2 — IMAGE PIPELINE

Build:
- image upload
- validation
- quality check
- preprocessing

Verify:

Upload
→ Quality Result

## MILESTONE 3 — AI INFERENCE

Add:
- YOLOv8-seg integration
- configurable checkpoint
- CPU inference
- segmentation visualization

Verify:

Image
→ YOLO
→ Detection + Mask

## MILESTONE 4 — MEASUREMENT

Add:
- mask post-processing
- crack length
- crack width
- crack area
- calibration/uncalibrated handling

Verify:

Mask
→ Measurements

## MILESTONE 5 — CONDITION ASSESSMENT

Add:
- configurable scoring rules
- Mild/Moderate/Severe result

Verify:

Measurements
→ Condition Score

## MILESTONE 6 — DATABASE & HISTORY

Add:
- walls
- inspections
- detections
- reports
- history
- comparison

Verify:

Inspection
→ Supabase
→ History

## MILESTONE 7 — RAG

Add:
- knowledge ingestion
- embeddings API
- pgvector
- retrieval
- LLM API
- citation validation

Verify:

Inspection
→ Evidence Retrieval
→ LLM
→ Cited Report

## MILESTONE 8 — FULL END-TO-END

Verify the complete workflow:

Upload
→ Quality Check
→ Preprocessing
→ YOLOv8-seg
→ Post-Processing
→ Measurement
→ Condition Assessment
→ Supabase
→ RAG
→ Report
→ History

## MILESTONE 9 — TESTING & REVIEW 2

Prepare:
- unit tests
- integration tests
- end-to-end test
- measured processing times
- known limitations
- screenshots
- architecture diagram
- database evidence
- actual model output
- actual report output

Do not report unmeasured performance.

---

# 14. SUCCESS CRITERIA

The project is considered successfully integrated when a reviewer can perform:

1. Select/create a wall.
2. Upload a real wall image.
3. Receive a real quality-check result.
4. Run the trained YOLOv8-seg checkpoint.
5. See segmentation output.
6. See calculated measurements.
7. Receive a condition assessment.
8. Save the inspection in Supabase.
9. Reopen the inspection from history.
10. Generate an evidence-backed RAG report.
11. See valid citations.
12. Review the complete result in the React interface.

The system must demonstrate one real continuous workflow rather than a collection of disconnected modules.

---

# 15. IMPORTANT LIMITATIONS

The application must clearly communicate:

- visible surface damage only
- internal/subsurface damage is not assessed
- physical measurement requires suitable calibration
- image quality affects results
- heritage-specific training data is important
- false positives are possible
- RAG depends on curated evidence
- expert review may be required

Never market the system as an autonomous structural safety certification tool.

# 16. PROJECT CONTEXT & HANDOVER

The project root must contain:

`PROJECT_CONTEXT.md`

This file is the persistent project handover/state document.

It must be updated after every meaningful implementation milestone, architectural decision, major bug fix, or change in project direction.

The purpose of this file is to allow another AI coding agent, developer, or team member to understand the current state of the project without reading the entire conversation history.

## PROJECT_CONTEXT.md MUST CONTAIN

### 1. Project Summary
Brief description of AWIS-HM and its purpose.

### 2. Current Architecture
Current working architecture and how the components communicate.

### 3. Current Technology Stack
Technologies actually being used, not merely planned technologies.

### 4. Current Implementation Status
For every major component, record:

- Status: Not Started / In Progress / Working / Needs Fix / Completed
- What is currently implemented
- What has been tested
- Known limitations

### 5. Current Milestone
Record:

- current milestone
- milestone objective
- work completed
- work remaining

### 6. What Was Built
Record important files, modules, APIs, database tables, services and interfaces that currently exist.

### 7. Important Decisions
Record architectural and implementation decisions that future agents must not accidentally undo.

Example:

- Supabase is used instead of local PostgreSQL.
- Google Colab is used for model training.
- Trained `.pt` checkpoint is used for local inference.
- RAG uses external embedding and LLM APIs.
- Local runtime must support CPU inference.

### 8. Environment & Run Instructions
Record:

- how to start frontend
- how to start backend
- environment variables required
- database setup
- important commands
- ports currently used

### 9. Testing Status
Record:

- tests implemented
- tests passed
- tests failed
- manual verification performed
- known issues

### 10. Known Problems / Blockers
Record active bugs, missing dependencies, unavailable model checkpoints, API limitations, or unresolved decisions.

### 11. Next Immediate Task
State exactly what should be implemented next.

This must be specific enough that a new coding agent can continue without guessing.

### 12. Change Log
Maintain a concise chronological record:

Date
→ What changed
→ Why
→ Result

## UPDATE RULE

After completing each milestone:

1. Update `PROJECT_CONTEXT.md`.
2. Record what actually works.
3. Record what does not work.
4. Record commands used for verification.
5. Record the next immediate task.
6. Never claim a feature is working unless it has actually been tested.

If another AI agent starts working on the project, it must read:

1. `agent.md`
2. `PROJECT_CONTEXT.md`
3. `Final_Draft_Rewritten.docx`

before modifying the project.

`PROJECT_CONTEXT.md` describes the current implementation state.

`Final_Draft_Rewritten.docx` describes the project specification and research basis.

If the implementation differs from the final draft, record the difference explicitly in `PROJECT_CONTEXT.md`.

# 17. UI DESIGN SYSTEM

The application must use a consistent professional heritage-engineering visual theme.

Design direction:

- dark charcoal base
- warm stone/earth accents
- restrained terracotta accents
- clean engineering-dashboard layout
- high readability
- minimal visual effects

Suggested palette:

- Background: #111315
- Secondary Background: #1B1E21
- Cards: #24282B
- Primary Text: #F1EEE8
- Secondary Text: #A9AAA6
- Stone Accent: #C7B89A
- Terracotta Accent: #9A6048
- Success: #657B5B
- Warning: #B08A4A
- Error: #A6534D
- Border: #3A3D3F

Do not use:

- neon colors
- cyberpunk styling
- excessive gradients
- excessive glassmorphism
- unnecessary animations
- decorative elements that reduce usability

Prioritize:

- inspection-result readability
- image/mask visualization
- measurement visibility
- clear condition status
- clean navigation
- consistent spacing
- responsive design

Do not use emojis in the application UI, generated reports, logs, documentation, or developer-facing output.