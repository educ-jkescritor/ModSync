from __future__ import annotations

import json
from typing import Any


def detect_technologies_dynamically(
    client: Any, model: str, text_pages: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """
    Uses the text LLM to dynamically scan page texts for outdated, deprecated, legacy,
    or reviewable concepts and technologies, returning page-by-page detections.
    """
    from .openai_client import generate_json_with_retry

    # Batch pages to minimize LLM roundtrips. 10 pages per batch is a good balance.
    batch_size = 10
    detections = []

    for i in range(0, len(text_pages), batch_size):
        batch = text_pages[i : i + batch_size]

        # Prepare page texts representation
        pages_content = []
        for p in batch:
            p_num = p.get("page", 0)
            p_text = p.get("text", "") or ""
            # Truncate page text if extremely long to avoid context bloat
            if len(p_text) > 2000:
                p_text = p_text[:2000] + "... [truncated]"
            pages_content.append(f"--- START PAGE {p_num} ---\n{p_text}\n--- END PAGE {p_num} ---")

        prompt = (
            "You are an expert curriculum reviewer. Analyze the text of the following pages from an educational module.\n"
            "Identify the main concepts, technologies, frameworks, libraries, standards, tools, or methodologies taught on these pages.\n\n"
            "For each key concept identified, return: \n"
            "1. The page number where it is mentioned.\n"
            "2. The exact name of the concept or technology.\n"
            "3. The alias/text matching the mention.\n"
            "4. A brief reason/context of why it is key to the page.\n\n"
            "Here are the pages:\n" + "\n\n".join(pages_content) + "\n\n"
            "Return a JSON object containing a list under the key \"detections\". Example format:\n"
            "{\n"
            "  \"detections\": [\n"
            "    {\n"
            "      \"page\": 5,\n"
            "      \"technology\": \"modular arithmetic\",\n"
            "      \"alias\": \"modular arithmetic\",\n"
            "      \"reason\": \"Taught as the core mathematical relation for the week.\"\n"
            "    }\n"
            "  ]\n"
            "}"
        )

        try:
            res = generate_json_with_retry(
                client,
                model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional educational curriculum validator. Only output valid JSON.",
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                temperature=0.1,
            )

            raw_detections = res.get("detections", [])
            for rd in raw_detections:
                p_num = rd.get("page")
                tech = rd.get("technology")
                alias = rd.get("alias") or tech
                if p_num is not None and tech:
                    # Map to the format expected by the pipeline
                    detections.append({
                        "technology": tech,
                        "alias": alias,
                        "page": int(p_num),
                        "start": 0,
                        "end": len(alias),
                        "category": "Technology",
                        "lifecycle_risk": 10,  # Default risk for reviewable items
                    })
        except Exception as exc:
            print(f"Error in dynamic pre-detection for batch {i//batch_size + 1}: {exc}")

    return detections
