from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any

from .knowledge_base import load_technology_kb


@dataclass(frozen=True)
class TechnologyDetection:
    technology: str
    alias: str
    page: int
    start: int
    end: int
    category: str
    lifecycle_risk: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def detect_technologies(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    entries = load_technology_kb()
    detections = _detect_with_flashtext(pages, entries)
    if detections is None:
        detections = _detect_with_regex(pages, entries)
    return [detection.to_dict() for detection in detections]


def _detect_with_flashtext(
    pages: list[dict[str, Any]], entries: list[dict[str, Any]]
) -> list[TechnologyDetection] | None:
    try:
        from flashtext import KeywordProcessor
    except ImportError:
        return None

    processor = KeywordProcessor(case_sensitive=False)
    entry_by_alias: dict[str, dict[str, Any]] = {}

    for entry in entries:
        for alias in [entry["name"], *entry.get("aliases", [])]:
            processor.add_keyword(alias, alias)
            entry_by_alias[alias.lower()] = entry

    detections: list[TechnologyDetection] = []
    for page in pages:
        page_number = int(page.get("page", 0))
        text = page.get("text", "") or ""
        for alias, start, end in processor.extract_keywords(text, span_info=True):
            entry = entry_by_alias.get(alias.lower())
            if not entry:
                continue
            detections.append(
                TechnologyDetection(
                    technology=entry["name"],
                    alias=alias,
                    page=page_number,
                    start=start,
                    end=end,
                    category=entry["category"],
                    lifecycle_risk=int(entry["lifecycle_risk"]),
                )
            )
    return detections


def _detect_with_regex(
    pages: list[dict[str, Any]], entries: list[dict[str, Any]]
) -> list[TechnologyDetection]:
    patterns: list[tuple[re.Pattern[str], str, dict[str, Any]]] = []

    for entry in entries:
        aliases = [entry["name"], *entry.get("aliases", [])]
        aliases.sort(key=len, reverse=True)
        for alias in aliases:
            pattern = re.compile(
                rf"(?<![A-Za-z0-9+#]){_alias_pattern(alias)}(?![A-Za-z0-9+#])",
                re.IGNORECASE,
            )
            patterns.append((pattern, alias, entry))

    detections: list[TechnologyDetection] = []
    seen_occurrences: set[tuple[int, str, int, int]] = set()

    for page in pages:
        page_number = int(page.get("page", 0))
        text = page.get("text", "") or ""
        for pattern, alias, entry in patterns:
            for match in pattern.finditer(text):
                key = (page_number, entry["name"], match.start(), match.end())
                if key in seen_occurrences:
                    continue
                seen_occurrences.add(key)
                detections.append(
                    TechnologyDetection(
                        technology=entry["name"],
                        alias=match.group(0),
                        page=page_number,
                        start=match.start(),
                        end=match.end(),
                        category=entry["category"],
                        lifecycle_risk=int(entry["lifecycle_risk"]),
                    )
                )

    detections.sort(key=lambda item: (item.page, item.start, item.technology))
    return detections


def _alias_pattern(alias: str) -> str:
    escaped = re.escape(alias.strip())
    return re.sub(r"\\\s+", r"\\s+", escaped)
