from __future__ import annotations

import os
import tempfile
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db, save_report
from .services.pdf_parser import extract_pdf_pages
from .services.report_pipeline import build_review_report


app = FastAPI(title="Faculty Curriculum Review Assistant API", version="0.1.0")

allowed_origins = os.getenv(
    "CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/analyze")
async def analyze_pdf(file: UploadFile = File(...)) -> dict:
    filename = file.filename or "module.pdf"
    content_type = file.content_type or ""

    if not filename.lower().endswith(".pdf") and content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="The uploaded PDF is empty.")

    temp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(raw)
            temp_path = temp_file.name

        pages = extract_pdf_pages(temp_path)
        
        # Two-Tier Agentic Pipeline
        from .services.agentic_pipeline import build_review_report_agentic
        
        try:
            report = build_review_report_agentic(pages, filename=filename, file_size=len(raw))
        except Exception as e:
            # If the pipeline throws an HTTPException (like the Quota 429), re-raise it
            from fastapi import HTTPException
            if isinstance(e, HTTPException):
                raise e
            # Otherwise, return a clean 500 error instead of silently dropping the connection
            print(f"Pipeline crashed: {e}")
            raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
            
        upload_id = save_report(filename, len(raw), report)
        return {"id": upload_id, **report}
    finally:
        if temp_path:
            Path(temp_path).unlink(missing_ok=True)

