@echo off
echo Starting Faculty Curriculum Review Assistant...

echo [1/2] Starting Python Backend Server...
start cmd /k "cd backend && .\.venv\Scripts\activate.bat && uvicorn app.main:app --reload --port 8000"

echo [2/2] Starting Next.js Frontend Server...
start cmd /k "cd frontend && npm run dev"

echo Both servers are starting up! 
echo The website will be available at http://localhost:3000
