from __future__ import annotations

import re
from typing import Any


LAB_KEYWORDS = (
    "lab",
    "laboratory",
    "hands-on",
    "exercise",
    "activity",
    "project",
    "build",
    "implement",
)
LEARNING_KEYWORDS = (
    "students will",
    "learning outcome",
    "objective",
    "assessment",
    "module outcome",
    "lesson outcome",
    "demonstrate",
)


def extract_contexts(
    pages: list[dict[str, Any]], detections: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    text_by_page = {int(page.get("page", 0)): page.get("text", "") or "" for page in pages}
    contexts: list[dict[str, Any]] = []

    for detection in detections:
        page_number = int(detection["page"])
        text = text_by_page.get(page_number, "")
        sentence_spans = split_sentences_with_spans(text)
        match_sentence_index = find_sentence_index(sentence_spans, int(detection["start"]))
        window = sentence_window(sentence_spans, match_sentence_index)
        context_text = " ".join(sentence for sentence, _, _ in window)
        lowered = context_text.lower()

        contexts.append(
            {
                "technology": detection["technology"],
                "alias": detection["alias"],
                "page": page_number,
                "context": [sentence for sentence, _, _ in window],
                "context_text": context_text,
                "appears_in_lab": any(keyword in lowered for keyword in LAB_KEYWORDS),
                "appears_in_learning_activity": any(
                    keyword in lowered for keyword in LEARNING_KEYWORDS
                ),
            }
        )

    return contexts


def split_sentences_with_spans(text: str) -> list[tuple[str, int, int]]:
    spans: list[tuple[str, int, int]] = []
    for match in re.finditer(r"[^.!?\n]+(?:[.!?]+|$)", text, re.MULTILINE):
        sentence = re.sub(r"\s+", " ", match.group(0)).strip()
        if sentence:
            spans.append((sentence, match.start(), match.end()))
    if not spans and text.strip():
        cleaned = re.sub(r"\s+", " ", text).strip()
        spans.append((cleaned, 0, len(text)))
    return spans


def find_sentence_index(sentence_spans: list[tuple[str, int, int]], start: int) -> int:
    for index, (_, sentence_start, sentence_end) in enumerate(sentence_spans):
        if sentence_start <= start <= sentence_end:
            return index
    return 0


def sentence_window(
    sentence_spans: list[tuple[str, int, int]], match_sentence_index: int
) -> list[tuple[str, int, int]]:
    if not sentence_spans:
        return []
    start = max(match_sentence_index - 1, 0)
    end = min(match_sentence_index + 2, len(sentence_spans))
    return sentence_spans[start:end]

