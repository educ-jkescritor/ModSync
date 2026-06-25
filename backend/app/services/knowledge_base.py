from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "technologies.json"


@lru_cache(maxsize=1)
def load_technology_kb() -> list[dict[str, Any]]:
    with DATA_PATH.open("r", encoding="utf-8") as handle:
        entries: list[dict[str, Any]] = json.load(handle)

    for entry in entries:
        entry.setdefault("aliases", [])
        entry.setdefault("category", "Technology")
        entry.setdefault("lifecycle_risk", 10)
        entry.setdefault("official_documentation", [])
        entry.setdefault("learning_resources", [])
    return entries


@lru_cache(maxsize=1)
def technology_by_name() -> dict[str, dict[str, Any]]:
    return {entry["name"]: entry for entry in load_technology_kb()}

