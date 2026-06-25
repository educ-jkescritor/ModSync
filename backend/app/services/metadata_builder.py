from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from .knowledge_base import technology_by_name


def build_metadata(
    detections: list[dict[str, Any]], contexts: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    kb = technology_by_name()
    frequency = Counter(detection["technology"] for detection in detections)
    pages_by_technology: dict[str, set[int]] = defaultdict(set)
    contexts_by_technology: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for detection in detections:
        pages_by_technology[detection["technology"]].add(int(detection["page"]))

    for context in contexts:
        contexts_by_technology[context["technology"]].append(context)

    metadata: list[dict[str, Any]] = []
    for technology, count in frequency.items():
        entry = kb[technology]
        related_contexts = contexts_by_technology[technology]
        sample_contexts = [
            {
                "page": item["page"],
                "context": item["context"],
                "context_text": item["context_text"],
                "appears_in_lab": item["appears_in_lab"],
                "appears_in_learning_activity": item["appears_in_learning_activity"],
            }
            for item in related_contexts[:3]
        ]

        metadata.append(
            {
                "technology": technology,
                "category": entry["category"],
                "frequency": count,
                "pages": sorted(pages_by_technology[technology]),
                "sample_contexts": sample_contexts,
                "appears_in_labs": any(item["appears_in_lab"] for item in related_contexts),
                "appears_in_learning_activities": any(
                    item["appears_in_learning_activity"] for item in related_contexts
                ),
                "lifecycle_risk": int(entry["lifecycle_risk"]),
                "lifecycle_status": entry["lifecycle_status"],
                "official_documentation": entry["official_documentation"],
                "learning_resources": entry["learning_resources"],
            }
        )

    metadata.sort(key=lambda item: (-item["frequency"], item["technology"]))
    return metadata
