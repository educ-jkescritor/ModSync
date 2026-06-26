from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

# Add project root to path
BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.database import connect, init_db

def export_finetuning_data():
    init_db()
    output_dir = BACKEND_ROOT / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    openai_path = output_dir / "finetune_openai.jsonl"
    gemini_path = output_dir / "finetune_gemini.jsonl"
    
    try:
        conn = connect()
        cursor = conn.cursor()
        cursor.execute("SELECT technology, decision, faculty_rationale, original_recommendation, created_at FROM feedback_logs")
        rows = cursor.fetchall()
    except Exception as exc:
        print(f"Error accessing database: {exc}")
        print("Please ensure reviews.sqlite3 exists and contains logged feedback.")
        return

    if not rows:
        print("No feedback logs found. Run the frontend, review some recommendations, submit approvals/rejections, and run this script again.")
        return

    openai_samples = []
    gemini_samples = []

    for row in rows:
        tech = row["technology"]
        decision = row["decision"]
        rationale = row["faculty_rationale"] or "No rationale provided."
        orig_rec = row["original_recommendation"]

        # Parse original recommendation JSON if possible
        try:
            orig_data = json.loads(orig_rec)
        except Exception:
            orig_data = {"technology": tech, "recommendation": orig_rec}

        # Build target alignment based on faculty validation
        target_recommendation = {
            "technology": tech,
            "validation_decision": decision,
            "faculty_rationale": rationale,
            "review_priority": "Low" if decision == "Reject" else orig_data.get("review_priority", "Medium"),
            "suggested_faculty_action": (
                f"REJECTED/IGNORE: {rationale}" if decision == "Reject"
                else (f"MODIFIED: {rationale}" if decision == "Modify" else orig_data.get("suggested_faculty_action"))
            )
        }

        # 1. OpenAI Fine-tuning format (messages JSONL)
        openai_sample = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are ModSync's Faculty Recommendation Agent. Align your recommendations with historical faculty review approvals/rejections."
                },
                {
                    "role": "user",
                    "content": f"Analyze technology: {tech}. Original suggestion: {json.dumps(orig_data)}"
                },
                {
                    "role": "assistant",
                    "content": json.dumps(target_recommendation)
                }
            ]
        }
        openai_samples.append(openai_sample)

        # 2. Gemini Fine-tuning format (contents JSONL)
        gemini_sample = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": f"Evaluate tech: {tech}. Context: {json.dumps(orig_data)}"}]
                },
                {
                    "role": "model",
                    "parts": [{"text": json.dumps(target_recommendation)}]
                }
            ]
        }
        gemini_samples.append(gemini_sample)

    # Write files
    with open(openai_path, "w", encoding="utf-8") as f:
        for sample in openai_samples:
            f.write(json.dumps(sample) + "\n")

    with open(gemini_path, "w", encoding="utf-8") as f:
        for sample in gemini_samples:
            f.write(json.dumps(sample) + "\n")

    print(f"Successfully exported {len(rows)} samples!")
    print(f"  - OpenAI format: {openai_path}")
    print(f"  - Gemini format: {gemini_path}")

if __name__ == "__main__":
    export_finetuning_data()
