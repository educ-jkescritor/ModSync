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
from fastapi.staticfiles import StaticFiles

from .database import init_db, save_report, save_feedback
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

static_dir = Path(__file__).resolve().parent / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


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

        report = build_review_report(temp_path, filename=filename, file_size=len(raw))
        upload_id = save_report(filename, len(raw), report)
        return {"id": upload_id, **report}
    finally:
        if temp_path:
            Path(temp_path).unlink(missing_ok=True)


from pydantic import BaseModel


class FeedbackPayload(BaseModel):
    upload_id: int | None = None
    technology: str
    decision: str
    faculty_rationale: str | None = None
    original_recommendation: str

@app.post("/api/feedback")
def submit_feedback(payload: FeedbackPayload) -> dict[str, str]:
    try:
        save_feedback(
            upload_id=payload.upload_id,
            technology=payload.technology,
            decision=payload.decision,
            rationale=payload.faculty_rationale,
            original_recommendation=payload.original_recommendation
        )
        return {"status": "success", "message": "Feedback recorded successfully."}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


