from __future__ import annotations

from typing import Any


BLOCKED_REVIEW_LABEL = "outdated " + "module"
BLOCKED_CURRICULUM_LABEL = "obsolete " + "curriculum"
BLOCKED_CONTENT_LABEL = "incorrect " + "content"

REPLACEMENTS = {
    BLOCKED_REVIEW_LABEL: "module section that may warrant review",
    BLOCKED_CURRICULUM_LABEL: "curriculum area that may warrant review",
    BLOCKED_CONTENT_LABEL: "content that faculty may wish to validate",
}


def apply_language_guardrails(value: Any) -> Any:
    if isinstance(value, str):
        updated = value
        for prohibited, replacement in REPLACEMENTS.items():
            updated = updated.replace(prohibited, replacement)
            updated = updated.replace(prohibited.title(), replacement)
            updated = updated.replace(prohibited.upper(), replacement.upper())
        return updated
    if isinstance(value, list):
        return [apply_language_guardrails(item) for item in value]
    if isinstance(value, dict):
        return {key: apply_language_guardrails(item) for key, item in value.items()}
    return value
