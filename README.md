# Faculty Curriculum Review Assistant

A hackathon MVP for faculty-assistive curriculum review. Faculty upload a PDF module, the backend extracts text, detects technology references, builds context metadata, scores review candidates, and returns a report of recommendations for faculty validation.

The app is intentionally framed as decision support. It suggests content areas that may warrant faculty review; it does not make final curriculum decisions.

Each recommendation includes a priority rationale, page-level review reasons, specific faculty checks, and explainability for lifecycle, frequency, labs, and learning activity signals.

## Stack

- Frontend: Next.js, React, TypeScript, TailwindCSS, shadcn-style local UI components
- Backend: FastAPI, Python, SQLite
- PDF processing: PyMuPDF primary path, `pypdf` fallback
- Technology detection: dictionary matching with FlashText when installed, regex fallback
- AI analysis: OpenAI GPT-4o when `OPENAI_API_KEY` is configured, deterministic local fallback otherwise

## Project Structure

```text
backend/
  app/
    main.py
    database.py
    data/technologies.json
    services/
  db/schema.sql
  tests/
frontend/
  app/
  components/ui/
  lib/
scripts/
outputs/
```

## Setup

Backend:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

Frontend:

```powershell
cd frontend
npm.cmd install
copy .env.example .env.local
npm.cmd run dev
```

Open `http://localhost:3000`.

## OpenAI Configuration

The backend works without an API key by using local recommendations. To enable GPT analysis:

```powershell
$env:OPENAI_API_KEY="sk-..."
$env:OPENAI_MODEL="gpt-4o"
uvicorn app.main:app --reload --port 8000
```

## Demo Assets

Generate the example PDF and sample report:

```powershell
python scripts/create_demo_assets.py
```

Generated files:

- `outputs/example-module.pdf`
- `outputs/sample-review-output.json`
- `frontend/public/sample-review-output.json`

The frontend includes a `Demo report` button that loads the public sample JSON.

## Backend API

Health check:

```http
GET /health
```

Analyze a PDF:

```http
POST /api/analyze
Content-Type: multipart/form-data

file=<PDF>
```

## Test

The deterministic services can be tested without FastAPI or OpenAI installed:

```powershell
cd backend
python -m unittest discover -s tests
```

## 5-Minute Demo Flow

1. Start the backend and frontend.
2. Open the app and load `outputs/example-module.pdf`, or click `Demo report`.
3. Show the processing state.
4. Filter recommendations by priority.
5. Open a recommendation and point to priority rationale, page review reasons, score implications, resources, and the faculty validation badge.
