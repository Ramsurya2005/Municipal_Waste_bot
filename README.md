# Municipal Waste Bot / Municipal Issue Reporting System

An AI-assisted municipal complaint platform that supports:
- guided complaint filing,
- image-assisted issue reporting,
- geotag/location capture,
- department auto-routing,
- satellite verification workflows,
- and a modern Next.js chat frontend connected to a Python backend.

This repository contains the core Python system (Streamlit + data + AI logic) and now also supports a Next.js frontend connected through API routes.

---

## 1) What this project does

The project helps citizens report civic problems (potholes, garbage, drainage, streetlights, water leaks, etc.) and routes issues to the correct municipal department.

### Key capabilities
- AI complaint understanding using Gemini-backed logic (`smart_chatbot.py`)
- Complaint classification and department mapping (`classifier.py`, `config.py`)
- Rich complaint filing UI in Streamlit (`pages/00_file_complaint.py`)
- Optional photo-based context capture and AI-assisted issue extraction
- Location input via map click / coordinates / text
- Complaint tracking and admin dashboard pages (`pages/02_track_complaint.py`, `pages/01_admin_dashboard.py`)
- Satellite-assisted scan/verification pipeline (`satellite_*.py`, `pages/04_satellite_scan.py`)
- MySQL + SQLite support and migration utilities
- Next.js frontend + Python backend integration for chat and history APIs

---

## 2) High-level architecture

## A) Python application layer
- **Primary app UI**: Streamlit (`app.py` + `pages/*`)
- **AI engine**: `SmartChatbot` class in `smart_chatbot.py`
- **Classifier/routing**: `IssueClassifier` in `classifier.py` + department map in `config.py`
- **Auth/session helpers**: `auth.py`
- **Persistence**: `mysql_database.py` (primary), `sqlite_database.py` (fallback/legacy)

## B) Satellite subsystem
- **Realtime indexing/streaming**: `satellite_realtime_imaging.py`
- **Detection/scanning operations**: `satellite_detector.py`
- **Integration wrapper**: `satellite_integration.py`
- **Dashboard/tools**: `satellite_dashboard.py`, `pages/04_satellite_scan.py`
- **Configuration/index**: `satellite_config.json`, `satellite_images_index.json`

## C) Next.js + API integration
- Next.js UI lives in sibling folder: `../municipal-chatbot-nextjs`
- Frontend calls same-origin Next API routes (`/api/chat`, `/api/history`)
- Next routes proxy to Python backend (`http://localhost:5000`)
- Python adapter service implemented in this repo: `backend_api.py`

---

## 3) End-to-end request flow

### Chat flow (Next.js frontend)
1. User sends message from Next.js UI.
2. Frontend calls `POST /api/chat` (Next route).
3. Next route proxies to Python backend (`backend_api.py` → `/api/chat`).
4. Python backend uses `SmartChatbot.chat(...)`.
5. Response + metadata returned to frontend.
6. Session history available via `GET /api/history?session_id=...`.

### Complaint filing flow (Streamlit)
1. Citizen opens **File Complaint** page.
2. Provides profile + issue details via manual text or image path.
3. AI suggests issue type, priority, and follow-up prompts.
4. User marks location (map/cordinates/text).
5. Data saved to DB and complaint ID generated.
6. Complaint appears in tracking/admin views.

### Satellite verification flow
1. Scan location or image batch.
2. Detector class processes images and identifies visible civic anomalies.
3. Results exported to `detection_results/` and/or JSON index.
4. Optional verification included in complaint context.

---

## 4) Module and file function map

This section explains **what each major file does**.

## Core app & AI
- `app.py`  
  Main Streamlit app shell, session state bootstrapping, chat rendering, auth views, and page-level orchestration.

- `smart_chatbot.py`  
  `SmartChatbot` class. Handles AI chat logic, fallback logic, keyword routing, intent/service-type extraction, follow-up question generation, and conversational response composition.

- `classifier.py`  
  `IssueClassifier` for issue categorization and route hints (department/category/urgency-style outputs).

- `config.py`  
  Environment loading + central constants. Holds department keyword mapping, app metadata, and prompt templates.

- `auth.py`  
  User authentication helper(s): login/signup support and session-linked identity handling.

## Database and migration
- `mysql_database.py`  
  Main DB access layer for complaints and related records in MySQL.

- `sqlite_database.py`  
  SQLite implementation/fallback for local or legacy operation.

- `migrate_sqlite_to_mysql.py`  
  Migration utility from SQLite datasets to MySQL schema.

- `seed_demo_data.py`  
  Seeds sample/demo complaint data for testing.

## Streamlit pages
- `pages/00_file_complaint.py`  
  Primary AI-enhanced complaint intake workflow (multi-step, method selection, map/geotag support, validations).

- `pages/01_admin_dashboard.py`  
  Admin-level overview and status/volume/inspection dashboards.

- `pages/02_track_complaint.py`  
  Citizen complaint status lookup and timeline display.

- `pages/03_my_complaints.py`  
  User-centric complaint history and status cards.

- `pages/04_satellite_scan.py`  
  Satellite scan control UI (batch/stream/manual scan) and verification-oriented views.

## Satellite system
- `satellite_realtime_imaging.py`  
  Realtime image stream/index lifecycle and ingestion operations.

- `satellite_detector.py`  
  Image analysis/detection methods for local and streaming satellite sources.

- `satellite_integration.py`  
  Bridges detector and app-level use cases.

- `satellite_dashboard.py`  
  Alternative/dashboard-style satellite monitoring UI.

- `satellite_database.py`  
  Persistence utilities for satellite result history.

- `satellite_verifier.py`  
  Validation/verification logic for satellite evidence.

## Next.js integration support (in this repo)
- `backend_api.py`  
  FastAPI adapter for frontend integration. Implements:
  - `GET /health`
  - `POST /api/chat`
  - `GET /api/history`

- `start_fullstack.bat`  
  One-click script to run Python backend + Next.js frontend together.

## Utility/setup scripts
- `setup_mysql.py`, `complete_mysql_setup.bat`, `setup_mysql_service.bat`, `start_mysql.bat`, `start_mysql_and_migrate.bat`  
  MySQL setup/start/migration convenience scripts.

- `test_greeting_flow.py`, `test_realtime_imaging.py`  
  Functional test/demo scripts for conversational and satellite paths.

---

## 5) API contracts used by frontend

## `POST /api/chat`
Request:
```json
{
  "message": "There is garbage near central market",
  "session_id": "abc123"
}
```

Response:
```json
{
  "reply": "...assistant response...",
  "session_id": "abc123",
  "metadata": {
    "service_type": "complaint",
    "department": "Sanitation",
    "complaint_id": null,
    "extracted_info": {},
    "follow_up_questions": []
  }
}
```

## `GET /api/history?session_id=abc123`
Response:
```json
[
  {
    "role": "user",
    "content": "...",
    "timestamp": "2026-03-25T15:50:01Z"
  },
  {
    "role": "assistant",
    "content": "...",
    "timestamp": "2026-03-25T15:50:02Z"
  }
]
```

---

## 6) Setup and run

## Prerequisites
- Python 3.10+
- Node.js 18+
- MySQL 8.x (if using MySQL path)

## Install Python dependencies
From this folder:
```bash
pip install -r requirements.txt
```

## Configure environment
Create/edit `.env` in this folder with at least:
```env
GEMINI_API_KEY=your_key
MYSQL_HOST=localhost
MYSQL_PORT=3307
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=municipal_chatbot
```

## Run Streamlit app (legacy/full Python UI)
```bash
streamlit run app.py
```

## Run FastAPI adapter (for Next.js integration)
```bash
python backend_api.py
```

## Run Next.js frontend
From sibling folder `municipal-chatbot-nextjs`:
```bash
npm install
npm run dev
```

or use one-click launcher from this repo:
```bash
start_fullstack.bat
```

---

## 7) Project data folders

- `user_images/` → uploaded complaint photos
- `detection_results/` → generated satellite detection outputs
- `satellite_images/` / `satellite images/` → satellite source datasets
- `mysql_data/` → local MySQL data directory (not for git)

---

## 8) Troubleshooting

## Frontend has no CSS
- Stop Next dev server
- Delete `.next` in Next.js folder
- Restart `npm run dev`

## Hydration mismatch in Next.js
- Ensure client-only stores/components are guarded until mount
- Restart after clearing `.next`

## Backend not connected
- Ensure Python API is running on `http://localhost:5000`
- Verify Next env values:
  - `PYTHON_BACKEND_URL=http://localhost:5000`
  - `NEXT_PUBLIC_PYTHON_BACKEND_URL=http://localhost:5000`

## Streamlit port conflicts
- Kill old process on port `8501`
- Restart Streamlit

---

## 9) Current status

- AI-guided complaint workflow: ✅
- Image-assisted report path: ✅
- Geotag/location capture: ✅
- Satellite subsystem integration: ✅
- Next.js ↔ Python backend connectivity: ✅

---

## 10) Repository notes

This repository now contains the Python core + integration backend.
The Next.js frontend lives in a sibling folder and communicates via the adapter endpoints described above.

If you want to make this a mono-repo in future, move `municipal-chatbot-nextjs` inside this root and update paths in `start_fullstack.bat`.
