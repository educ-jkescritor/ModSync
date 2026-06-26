from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any


BACKEND_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = BACKEND_ROOT / "db" / "schema.sql"
DEFAULT_DB_PATH = BACKEND_ROOT / "data" / "reviews.sqlite3"


def connect() -> sqlite3.Connection:
    db_path = Path(os.getenv("FACULTY_REVIEW_DB", str(DEFAULT_DB_PATH)))
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with connect() as connection:
        schema = SCHEMA_PATH.read_text(encoding="utf-8")
        connection.executescript(schema)


def save_report(filename: str, file_size: int, report: dict[str, Any]) -> int:
    init_db()
    with connect() as connection:
        cursor = connection.execute(
            "INSERT INTO uploads (filename, file_size, pages_analyzed) VALUES (?, ?, ?)",
            (filename, file_size, int(report["pages_analyzed"])),
        )
        upload_id = int(cursor.lastrowid)

        for detection in report["detections"]:
            connection.execute(
                """
                INSERT INTO detections (
                  upload_id, technology, alias, page, start_offset, end_offset, category, lifecycle_risk
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    upload_id,
                    detection["technology"],
                    detection["alias"],
                    detection["page"],
                    detection["start"],
                    detection["end"],
                    detection["category"],
                    detection["lifecycle_risk"],
                ),
            )

        for recommendation in report["recommendations"]:
            connection.execute(
                """
                INSERT INTO recommendations (
                  upload_id, technology, review_priority, priority_score, confidence_score,
                  pages_json, recommendation_json, faculty_validation_required
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    upload_id,
                    recommendation["technology"],
                    recommendation["review_priority"],
                    recommendation["priority_score"],
                    float(recommendation["confidence_score"]),
                    json.dumps(recommendation["pages"]),
                    json.dumps(recommendation),
                    1 if recommendation.get("faculty_validation_required", True) else 0,
                ),
            )
        connection.commit()
        return upload_id


def save_feedback(
    upload_id: int | None,
    technology: str,
    decision: str,
    faculty_rationale: str | None,
    original_recommendation: dict[str, Any],
) -> None:
    init_db()
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO feedback_logs (
                upload_id, technology, decision, faculty_rationale, original_recommendation
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                upload_id,
                technology,
                decision,
                faculty_rationale,
                json.dumps(original_recommendation),
            ),
        )
        connection.commit()


def get_feedback_dataset() -> list[dict[str, Any]]:
    init_db()
    records = []
    with connect() as connection:
        cursor = connection.execute(
            "SELECT upload_id, technology, decision, faculty_rationale, original_recommendation, created_at FROM feedback_logs ORDER BY id ASC"
        )
        for row in cursor:
            try:
                orig_rec = json.loads(row["original_recommendation"])
            except Exception:
                orig_rec = row["original_recommendation"]
            records.append({
                "upload_id": row["upload_id"],
                "technology": row["technology"],
                "decision": row["decision"],
                "faculty_rationale": row["faculty_rationale"],
                "original_recommendation": orig_rec,
                "created_at": row["created_at"],
            })
    return records


