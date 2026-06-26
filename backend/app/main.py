from __future__ import annotations

import json
import io
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
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any

from .database import init_db, save_report, save_feedback, get_feedback_dataset
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


class FeedbackRequest(BaseModel):
    upload_id: Optional[int] = None
    technology: str
    decision: str
    faculty_rationale: Optional[str] = None
    original_recommendation: Dict[str, Any]


@app.post("/api/feedback")
def submit_feedback(payload: FeedbackRequest) -> dict[str, str]:
    try:
        save_feedback(
            upload_id=payload.upload_id,
            technology=payload.technology,
            decision=payload.decision,
            faculty_rationale=payload.faculty_rationale,
            original_recommendation=payload.original_recommendation,
        )
        return {"status": "success", "message": "Feedback recorded successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/export-finetuning")
def export_finetuning() -> StreamingResponse:
    try:
        records = get_feedback_dataset()
        output = io.BytesIO()
        for rec in records:
            chat_format = {
                "messages": [
                    {
                        "role": "system",
                        "content": "You are ModSync, an AI curriculum review assistant. You analyze course modules for legacy technologies and suggest modern replacements. Adjust recommendations based on faculty alignment feedback.",
                    },
                    {
                        "role": "user",
                        "content": f"Technology: {rec['technology']}\nOriginal Recommendation:\n{json.dumps(rec['original_recommendation'], indent=2)}",
                    },
                    {
                        "role": "assistant",
                        "content": f"Decision: {rec['decision']}\nFaculty Rationale: {rec['faculty_rationale'] or 'No rationale provided.'}",
                    },
                ]
            }
            output.write((json.dumps(chat_format) + "\n").encode("utf-8"))

        output.seek(0)
        return StreamingResponse(
            output,
            media_type="application/x-jsonlines",
            headers={
                "Content-Disposition": "attachment; filename=modsync_finetuning_dataset.jsonl"
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


