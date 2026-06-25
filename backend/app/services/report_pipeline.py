from __future__ import annotations

from typing import Any

from .context_extraction import extract_contexts
from .metadata_builder import build_metadata
from .openai_review import analyze_candidate
from .scoring import score_candidates
from .technology_detection import detect_technologies


def build_review_report(
    pages: list[dict[str, Any]], filename: str | None = None, file_size: int | None = None
) -> dict[str, Any]:
    detections = detect_technologies(pages)
    contexts = extract_contexts(pages, detections)
    metadata = build_metadata(detections, contexts)
    candidates = score_candidates(metadata)
    recommendations = [analyze_candidate(candidate) for candidate in candidates]

    return {
        "filename": filename,
        "file_size": file_size,
        "pages_analyzed": len(pages),
        "detections": detections,
        "metadata": metadata,
        "recommendations": recommendations,
        "summary": {
            "technology_count": len(metadata),
            "review_candidate_count": len(recommendations),
            "high_priority_count": sum(
                1 for item in recommendations if item.get("review_priority") == "High"
            ),
            "medium_priority_count": sum(
                1 for item in recommendations if item.get("review_priority") == "Medium"
            ),
            "low_priority_count": sum(
                1 for item in recommendations if item.get("review_priority") == "Low"
            ),
        },
    }

