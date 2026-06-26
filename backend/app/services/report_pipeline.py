from __future__ import annotations

from pathlib import Path
from typing import Any

from .pdf_to_images import convert_pdf_to_images
from .gemini_client import get_gemini_client, get_gemini_model
from ..agents.extraction_agent import extract_page_contents
from ..agents.validation_agent import validate_concepts
from ..agents.recommendation_agent import generate_recommendations
from ..agents.migration_agent import generate_migration_plan
from .language_guardrails import apply_language_guardrails

# For backward compatibility with the test suite (old list of page dicts)
from .context_extraction import extract_contexts
from .metadata_builder import build_metadata
from .openai_review import analyze_candidate
from .scoring import score_candidates
from .technology_detection import detect_technologies


import uuid

def save_pdf_page_images(pdf_path: str | Path) -> tuple[str, list[bytes]]:
    upload_uuid = str(uuid.uuid4())
    static_dir = Path(__file__).resolve().parents[1] / "static" / upload_uuid
    static_dir.mkdir(parents=True, exist_ok=True)
    
    page_images = []
    try:
        from .pdf_to_images import convert_pdf_to_images
        page_images = convert_pdf_to_images(pdf_path)
        for idx, img_bytes in enumerate(page_images, start=1):
            img_path = static_dir / f"page_{idx}.png"
            img_path.write_bytes(img_bytes)
    except Exception as exc:
        print(f"Error saving PDF page images: {exc}")
        
    return upload_uuid, page_images


def build_review_report(
    pdf_path_or_pages: str | Path | list[dict[str, Any]],
    filename: str | None = None,
    file_size: int | None = None
) -> dict[str, Any]:
    """
    Builds the curriculum review report.
    Supports either:
    1. A list of page dictionaries (backward compatibility for testing or simple text fallback).
    2. A file path to a PDF (triggering the multimodal agentic pipeline).
    """
    import os
    if isinstance(pdf_path_or_pages, list):
        return _build_old_report(pdf_path_or_pages, filename, file_size)

    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        print("Warning: GEMINI_API_KEY not found in environment. Falling back to offline text-based parsing.")
        upload_uuid, _ = save_pdf_page_images(pdf_path_or_pages)
        from .pdf_parser import extract_pdf_pages
        pages = extract_pdf_pages(pdf_path_or_pages)
        return _build_old_report(pages, filename, file_size, upload_uuid)

    try:
        return _build_multimodal_report(pdf_path_or_pages, filename, file_size)
    except Exception as exc:
        print(f"Error in multimodal report: {exc}. Falling back to offline text-based parsing.")
        upload_uuid, _ = save_pdf_page_images(pdf_path_or_pages)
        from .pdf_parser import extract_pdf_pages
        pages = extract_pdf_pages(pdf_path_or_pages)
        return _build_old_report(pages, filename, file_size, upload_uuid)


def _build_old_report(
    pages: list[dict[str, Any]], filename: str | None = None, file_size: int | None = None, upload_uuid: str | None = None
) -> dict[str, Any]:
    detections = detect_technologies(pages)
    contexts = extract_contexts(pages, detections)
    metadata = build_metadata(detections, contexts)
    candidates = score_candidates(metadata)
    recommendations = [analyze_candidate(candidate) for candidate in candidates]

    if upload_uuid:
        for rec in recommendations:
            if "page_review_reasons" in rec:
                for reason in rec["page_review_reasons"]:
                    reason["image_url"] = f"/static/{upload_uuid}/page_{reason['page']}.png"

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


def _build_multimodal_report(
    pdf_path: str | Path,
    filename: str | None = None,
    file_size: int | None = None
) -> dict[str, Any]:
    client = get_gemini_client()
    model = get_gemini_model()

    # 1. Convert PDF pages to PNG images and save them statically
    upload_uuid, page_images = save_pdf_page_images(pdf_path)

    # 2. Extract contents page-by-page using the Multimodal Extraction Agent
    import time
    page_extractions = []
    for idx, img_bytes in enumerate(page_images, start=1):
        if idx > 1:
            # Sleep 2 seconds between pages to respect rate limits of free tier
            time.sleep(2.0)
        extraction = extract_page_contents(client, model, idx, img_bytes)
        page_extractions.append(extraction)

    # 3. Aggregate detections by concept
    concept_map: dict[str, list[dict[str, Any]]] = {}
    for extraction in page_extractions:
        for c in extraction.concepts:
            name = c.name.strip()
            if not name:
                continue
            if name not in concept_map:
                concept_map[name] = []
            concept_map[name].append({
                "page": extraction.page,
                "role": c.role,
                "evidence": c.evidence
            })

    # 4. Prepare list for the Validation Agent
    concepts_to_validate = []
    for name, occurrences in concept_map.items():
        concepts_to_validate.append({
            "name": name,
            "occurrences": occurrences
        })

    # Run Validation Agent
    validation_res = validate_concepts(client, model, concepts_to_validate)

    # 5. Run Recommendation Agent
    recommendation_res = generate_recommendations(
        client,
        model,
        extractions=[e.model_dump() for e in page_extractions],
        validations=[v.model_dump() for v in validation_res.validations]
    )

    # 6. Map RecommendationResponse items to output schema
    recommendations = []
    if recommendation_res and recommendation_res.recommendations:
        for item in recommendation_res.recommendations:
            tech = item.technology
            val = next((v for v in validation_res.validations if v.concept == tech), None)
            status = val.status if val else "Current"
            doc_urls = val.official_documentation if val else []
            resource_urls = val.learning_resources if val else []

            page_nums = sorted(list(set(occ["page"] for occ in concept_map.get(tech, []))))
            if not page_nums:
                page_nums = sorted(list(set(p.page for p in item.page_review_reasons)))

            sample_contexts = []
            for p in item.page_review_reasons:
                page_occurrences = concept_map.get(tech, [])
                appears_in_lab = False
                appears_in_activity = False
                for occ in page_occurrences:
                    if occ["page"] == p.page:
                        role_lower = occ["role"].lower()
                        if "lab" in role_lower or "exercise" in role_lower or "assessment" in role_lower:
                            appears_in_lab = True
                        if "learning" in role_lower or "outcome" in role_lower or "objective" in role_lower or "main" in role_lower:
                            appears_in_activity = True

                if not page_occurrences:
                    focus_lower = p.review_focus.lower()
                    imp_lower = " ".join(p.implications).lower()
                    if "lab" in focus_lower or "exercise" in focus_lower or "lab" in imp_lower or "exercise" in imp_lower:
                        appears_in_lab = True
                    if "outcome" in focus_lower or "objective" in focus_lower or "outcome" in imp_lower or "objective" in imp_lower:
                        appears_in_activity = True

                sample_contexts.append({
                    "page": p.page,
                    "context": [p.context_text],
                    "context_text": p.context_text,
                    "appears_in_lab": appears_in_lab,
                    "appears_in_learning_activity": appears_in_activity
                })

            explainability = [
                {
                    "factor": "Lifecycle",
                    "points": item.score_breakdown_lifecycle,
                    "max_points": 40,
                    "evidence": f"Lifecycle status is {status}.",
                    "implication": f"A lifecycle risk contribution of {item.score_breakdown_lifecycle} indicates a potential mismatch with modern standards.",
                    "review_question": "Should this concept be updated or replaced?"
                },
                {
                    "factor": "Frequency",
                    "points": item.score_breakdown_frequency,
                    "max_points": 30,
                    "evidence": f"Found across {len(page_nums)} page(s).",
                    "implication": "High frequency suggests the concept is a key dependency in this module.",
                    "review_question": "Does the course material reference this concept repeatedly?"
                },
                {
                    "factor": "Labs",
                    "points": item.score_breakdown_labs,
                    "max_points": 20,
                    "evidence": "Taught in laboratory context." if item.score_breakdown_labs > 0 else "No laboratory context detected.",
                    "implication": "Hands-on usage means students will encounter blockers if tools are deprecated.",
                    "review_question": "Do the students complete exercises with this technology?"
                },
                {
                    "factor": "Activities",
                    "points": item.score_breakdown_activities,
                    "max_points": 10,
                    "evidence": "Taught near learning activities." if item.score_breakdown_activities > 0 else "No learning activity context detected.",
                    "implication": "Assessment or learning outcomes might need updates if changed.",
                    "review_question": "Is this concept tied to course outcomes?"
                }
            ]

            page_review_reasons = [
                {
                    "page": p.page,
                    "context_text": p.context_text,
                    "reason": p.reason,
                    "review_focus": p.review_focus,
                    "implications": p.implications,
                    "image_url": f"/static/{upload_uuid}/page_{p.page}.png"
                }
                for p in item.page_review_reasons
            ]

            # Run Migration Agent to generate guides and code snippets
            migration_plan = generate_migration_plan(
                client=client,
                model=model,
                technology=tech,
                status=status,
                suggested_action=item.suggested_faculty_action
            )

            recommendations.append({
                "technology": tech,
                "review_priority": item.review_priority,
                "priority_score": item.priority_score,
                "confidence_score": item.confidence_score,
                "industry_observation": item.industry_observation,
                "why_suggested": item.why_suggested,
                "priority_rationale": item.priority_rationale,
                "suggested_faculty_action": item.suggested_faculty_action,
                "specific_recommendations": item.specific_recommendations,
                "page_review_reasons": page_review_reasons,
                "explainability": explainability,
                "official_documentation": doc_urls,
                "learning_resources": resource_urls,
                "faculty_validation_required": True,
                "sample_contexts": sample_contexts,
                "score_breakdown": {
                    "technology_lifecycle_risk": item.score_breakdown_lifecycle,
                    "frequency": item.score_breakdown_frequency,
                    "appears_in_labs": item.score_breakdown_labs,
                    "appears_in_learning_activities": item.score_breakdown_activities
                },
                "pages": page_nums,
                "frequency": len(page_nums),
                "ai_mode": model,
                "migration_guide": migration_plan.migration_guide,
                "migration_legacy_code": migration_plan.legacy_example,
                "migration_modern_code": migration_plan.modern_example,
                "migration_rationale_why_deprecated": migration_plan.why_deprecated,
                "migration_rationale_modern_benefits": migration_plan.modern_benefits
            })
    else:
        # Fallback if Recommendation Agent didn't produce anything
        for val in validation_res.validations:
            status = val.status
            tech = val.concept
            page_nums = sorted(list(set(occ["page"] for occ in concept_map.get(tech, []))))

            lifecycle_points = 40 if status == "Deprecated" else (30 if status == "Historical only" else (20 if status == "Legacy but still useful" else 0))
            frequency_points = min(len(page_nums) * 6, 30)

            appears_in_labs = any("lab" in occ["role"].lower() or "exercise" in occ["role"].lower() for occ in concept_map.get(tech, []))
            appears_in_activities = any("objective" in occ["role"].lower() or "outcome" in occ["role"].lower() for occ in concept_map.get(tech, []))

            lab_points = 20 if appears_in_labs else 0
            activity_points = 10 if appears_in_activities else 0

            total_score = min(lifecycle_points + frequency_points + lab_points + activity_points, 100)
            priority = "High" if total_score >= 75 else ("Medium" if total_score >= 45 else "Low")

            page_review_reasons = []
            sample_contexts = []
            for occ in concept_map.get(tech, []):
                reason_text = f"Review references to {tech} on page {occ['page']}, taught as {occ['role']}."
                page_review_reasons.append({
                    "page": occ["page"],
                    "context_text": occ["evidence"],
                    "reason": reason_text,
                    "review_focus": occ["role"],
                    "implications": [f"This concept is flagged as {status}."],
                    "image_url": f"/static/{upload_uuid}/page_{occ['page']}.png"
                })
                sample_contexts.append({
                    "page": occ["page"],
                    "context": [occ["evidence"]],
                    "context_text": occ["evidence"],
                    "appears_in_lab": "lab" in occ["role"].lower() or "exercise" in occ["role"].lower(),
                    "appears_in_learning_activity": "objective" in occ["role"].lower() or "outcome" in occ["role"].lower()
                })

            explainability = [
                {
                    "factor": "Lifecycle",
                    "points": lifecycle_points,
                    "max_points": 40,
                    "evidence": f"Lifecycle status is {status}.",
                    "implication": "Lifecycle risk dictates if the technology is EOL or legacy.",
                    "review_question": "Should this technology be updated or replaced?"
                },
                {
                    "factor": "Frequency",
                    "points": frequency_points,
                    "max_points": 30,
                    "evidence": f"Found across {len(page_nums)} page(s).",
                    "implication": "Mentions contribute to overall review urgency.",
                    "review_question": "Does the course material reference this concept repeatedly?"
                },
                {
                    "factor": "Labs",
                    "points": lab_points,
                    "max_points": 20,
                    "evidence": "Taught in laboratory context." if appears_in_labs else "No laboratory context detected.",
                    "implication": "Hands-on usage means students will encounter blockers if tools are deprecated.",
                    "review_question": "Do the students complete exercises with this technology?"
                },
                {
                    "factor": "Activities",
                    "points": activity_points,
                    "max_points": 10,
                    "evidence": "Taught near learning activities." if appears_in_activities else "No learning activity context detected.",
                    "implication": "Assessment or learning outcomes might need updates if changed.",
                    "review_question": "Is this concept tied to course outcomes?"
                }
            ]

            recommendations.append({
                "technology": tech,
                "review_priority": priority,
                "priority_score": total_score,
                "confidence_score": val.confidence,
                "industry_observation": f"The concept {tech} is considered {status}.",
                "why_suggested": f"It is taught as a {concept_map.get(tech, [{}])[0].get('role', 'concept')} and is currently {status}.",
                "priority_rationale": f"Scored {total_score}/100 based on its {status} status and instructional context.",
                "suggested_faculty_action": f"Evaluate whether {tech} remains appropriate for the curriculum, or replace/update it.",
                "specific_recommendations": [
                    f"Check whether {tech} should be updated or replaced.",
                    f"Refer to official documentation and learning resources."
                ],
                "page_review_reasons": page_review_reasons,
                "explainability": explainability,
                "official_documentation": val.official_documentation,
                "learning_resources": val.learning_resources,
                "faculty_validation_required": True,
                "sample_contexts": sample_contexts,
                "score_breakdown": {
                    "technology_lifecycle_risk": lifecycle_points,
                    "frequency": frequency_points,
                    "appears_in_labs": lab_points,
                    "appears_in_learning_activities": activity_points
                },
                "pages": page_nums,
                "frequency": len(page_nums),
                "ai_mode": model,
                "migration_guide": f"1. Identify references to {tech}.\n2. Update to a supported alternative.",
                "migration_legacy_code": f"# Outdated usage of {tech}",
                "migration_modern_code": "# Modern equivalent approach",
                "migration_rationale_why_deprecated": f"The use of {tech} is outdated and no longer aligns with modern industrial standards or security support practices.",
                "migration_rationale_modern_benefits": "Upgrading to a modern replacement improves safety, compiler/environment support, and student readiness for current industry roles."
            })

    # 7. Construct detections to return and save in DB
    detections = []
    for name, occurrences in concept_map.items():
        val_item = next((v for v in validation_res.validations if v.concept == name), None)
        status = val_item.status if val_item else "Current"
        lifecycle_risk = 10
        if status == "Deprecated":
            lifecycle_risk = 40
        elif status == "Historical only":
            lifecycle_risk = 30
        elif status == "Legacy but still useful":
            lifecycle_risk = 20

        for occ in occurrences:
            detections.append({
                "technology": name,
                "alias": name,
                "page": occ["page"],
                "start": 0,
                "end": len(occ["evidence"]),
                "category": "Technology" if name != "Unknown" else "General",
                "lifecycle_risk": lifecycle_risk
            })

    # Calculate counts for summary
    high_count = sum(1 for item in recommendations if item.get("review_priority") == "High")
    medium_count = sum(1 for item in recommendations if item.get("review_priority") == "Medium")
    low_count = sum(1 for item in recommendations if item.get("review_priority") == "Low")

    return apply_language_guardrails({
        "filename": filename,
        "file_size": file_size,
        "pages_analyzed": len(page_images),
        "detections": detections,
        "recommendations": recommendations,
        "summary": {
            "technology_count": len(concept_map),
            "review_candidate_count": len(recommendations),
            "high_priority_count": high_count,
            "medium_priority_count": medium_count,
            "low_priority_count": low_count,
        }
    })
