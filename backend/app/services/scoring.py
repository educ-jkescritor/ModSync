from __future__ import annotations

from typing import Any


def score_candidates(metadata: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = []
    for item in metadata:
        lifecycle_points = max(0, min(int(item["lifecycle_risk"]), 40))
        frequency_points = max(0, min(int(item["frequency"]) * 6, 30))
        lab_points = 20 if item["appears_in_labs"] else 0
        learning_points = 10 if item["appears_in_learning_activities"] else 0
        total = min(lifecycle_points + frequency_points + lab_points + learning_points, 100)

        candidate = {
            **item,
            "score_breakdown": {
                "technology_lifecycle_risk": lifecycle_points,
                "frequency": frequency_points,
                "appears_in_labs": lab_points,
                "appears_in_learning_activities": learning_points,
            },
            "priority_score": total,
            "review_priority": priority_label(total),
        }
        candidates.append(candidate)

    candidates.sort(key=lambda item: (-item["priority_score"], item["technology"]))
    return candidates


def priority_label(score: int) -> str:
    if score >= 75:
        return "High"
    if score >= 45:
        return "Medium"
    return "Low"

