from __future__ import annotations

import json
import os
from typing import Any

from .language_guardrails import apply_language_guardrails


SYSTEM_PROMPT = """You are an expert curriculum review assistant bridging academia and industry.

You help faculty identify portions of modules that may warrant review by analyzing how a technology is used, what modern industry practices are, and providing highly practical recommendations.

You will be given technology metadata which includes a pre-calculated `priority_score` (0-100), a `review_priority` (Low, Medium, or High), and a `score_breakdown`. The score is calculated based on:
- Technology Lifecycle Risk (up to 40 points)
- Frequency of mentions (up to 30 points)
- Appearance in labs (up to 20 points)
- Appearance in learning activities (up to 10 points)

Your task is to provide a rich, flexible analysis. Do NOT change the provided `review_priority` or `priority_score`.
CRITICAL: Keep all string responses (industry_observation, why_suggested, priority_rationale, etc.) extremely concise. Limit them to 1-2 direct sentences max. Avoid fluff.

Return a JSON object with the following keys:
- "review_priority": strictly use the value provided in the input.
- "industry_observation": string explaining what the industry is currently using as alternatives or modern standards in contrast/relation to this technology.
- "why_suggested": string explaining why this is flagged, explicitly referencing how the technology is used contextually in the module (e.g. is it in a lab? a passing mention?).
- "suggested_faculty_action": string providing a highly practical, actionable evaluation recommendation for the faculty (e.g. "Evaluate migrating this lab to X", "Add a disclaimer that this is legacy", etc).
- "specific_recommendations": array of strings with detailed, practical steps for faculty to evaluate or adapt the curriculum based on modern practices.
- "confidence_score": number between 0 and 1.
- "priority_rationale": string explaining how the score breakdown justifies the priority level.
- "page_review_reasons": array of objects detailing page-level context (include how it's used on the page).
- "explainability": array of objects breaking down lifecycle, frequency, labs, and learning activities.

Return JSON only."""


def analyze_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    openai_key = os.getenv("OPENAI_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")
    local = local_recommendation(candidate)
    
    if not openai_key and not gemini_key:
        print("Warning: Neither OPENAI_API_KEY nor GEMINI_API_KEY found. Using local fallback.")
        return apply_language_guardrails(local)

    try:
        from openai import OpenAI
        from google import genai
        from google.genai import types

        openai_client = OpenAI(api_key=openai_key) if openai_key else None
        gemini_client = genai.Client(api_key=gemini_key) if gemini_key else None
        
        models_to_try = []
        if openai_key:
            models_to_try.extend(["gpt-4o-mini", "gpt-4o"])
        if gemini_key:
            models_to_try.extend(["gemini-3.1-flash-lite", "gemini-3.1-pro-preview", "gemini-3.5-flash", "gemini-2.5-flash"])
            
        parsed = None
        last_exc = None
        for model in models_to_try:
            print(f"Sending request to AI provider ({model}) for {candidate['technology']}...")
            try:
                if model.startswith("gpt-"):
                    response = openai_client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": json.dumps(candidate, ensure_ascii=False)}
                        ],
                        response_format={"type": "json_object"},
                        temperature=0.2,
                    )
                    content = response.choices[0].message.content or "{}"
                else:
                    gemini_prompt = SYSTEM_PROMPT + "\n\n" + json.dumps(candidate, ensure_ascii=False)
                    response = gemini_client.models.generate_content(
                        model=model,
                        contents=gemini_prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            temperature=0.2,
                        )
                    )
                    content = response.text or "{}"
                
                parsed = json.loads(content)
                
                for key, value in local.items():
                    parsed.setdefault(key, value)
                
                parsed["ai_mode"] = model
                print(f"Successfully received analysis for {candidate['technology']} via {model}.")
                return apply_language_guardrails(parsed)
            except Exception as exc:
                error_msg = str(exc).lower()
                print(f"Model {model} failed with {error_msg}, trying next...")
                last_exc = exc
                continue
                    
        print(f"All AI API providers failed for {candidate['technology']}: {last_exc}")
        recommendation = local
        recommendation["ai_mode"] = "local_fallback"
        recommendation["fallback_reason"] = f"AI analysis was unavailable: {last_exc}"
        return apply_language_guardrails(recommendation)
        
    except Exception as outer_exc:
        print(f"Critical AI API initialization or execution failure: {outer_exc}")
        recommendation = local
        recommendation["ai_mode"] = "local_fallback"
        recommendation["fallback_reason"] = f"AI API init failure: {outer_exc}"
        return apply_language_guardrails(recommendation)

def local_recommendation(candidate: dict[str, Any]) -> dict[str, Any]:
    technology = candidate["technology"]
    priority = candidate["review_priority"]
    status = candidate["lifecycle_status"]
    pages = candidate["pages"]
    frequency = candidate["frequency"]
    
    lab_phrase = (
        " Since it appears in hands-on labs or exercises, students may encounter blockers if the tooling or setup is not current."
        if candidate.get("appears_in_labs", False)
        else ""
    )
    learning_phrase = (
        " Its proximity to learning outcomes suggests that any changes to this technology could require adapting the assessment rubrics."
        if candidate.get("appears_in_learning_activities", False)
        else ""
    )
    
    page_review_reasons = build_page_review_reasons(candidate)
    explainability = build_explainability(candidate)
    priority_rationale = build_priority_rationale(candidate, explainability)
    specific_recommendations = build_specific_recommendations(candidate, page_review_reasons)
    
    suggested_faculty_action = (
        specific_recommendations[0]
        if specific_recommendations
        else f"Evaluate whether {technology} is still the best tool to teach this concept, or if the module should be updated to reflect modern industry standards."
    )

    confidence = round(min(0.95, 0.55 + (candidate["priority_score"] / 200)), 2)

    return {
        "technology": technology,
        "review_priority": priority,
        "priority_score": candidate["priority_score"],
        "confidence_score": confidence,
        "industry_observation": status,
        "why_suggested": (
            f"{technology} was referenced {frequency} time(s) across page(s) {pages}. "
            f"{priority_rationale}"
            f"{lab_phrase}{learning_phrase}"
        ).strip(),
        "priority_rationale": priority_rationale,
        "suggested_faculty_action": suggested_faculty_action,
        "specific_recommendations": specific_recommendations,
        "page_review_reasons": page_review_reasons,
        "explainability": explainability,
        "current_technology_references": candidate.get("current_technology_references", []),
        "new_technology_references": candidate.get("new_technology_references", []),
        "faculty_validation_required": True,
        "sample_contexts": candidate["sample_contexts"],
        "score_breakdown": candidate["score_breakdown"],
        "pages": pages,
        "frequency": frequency,
        "ai_mode": "local_fallback",
    }


def build_priority_rationale(
    candidate: dict[str, Any], explainability: list[dict[str, Any]]
) -> str:
    priority = candidate["review_priority"].lower()
    strongest = sorted(explainability, key=lambda item: item["points"], reverse=True)
    reasons = [item["factor"].lower() for item in strongest if item["points"] > 0]
    
    if not reasons:
        return f"This technology is flagged as a {priority} priority due to its general presence in the module, though it currently presents minimal lifecycle or instructional risks."
    
    if len(reasons) == 1:
        reasons_str = reasons[0]
    else:
        reasons_str = ", ".join(reasons[:-1]) + " and " + reasons[-1]
        
    return f"This is considered a {priority} priority review primarily because of its {reasons_str}."


def build_page_review_reasons(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    reasons: list[dict[str, Any]] = []
    seen_pages: set[int] = set()

    for context in candidate["sample_contexts"]:
        page = int(context["page"])
        if page in seen_pages:
            continue
        seen_pages.add(page)

        context_text = context["context_text"]
        lab = bool(context.get("appears_in_lab"))
        learning = bool(context.get("appears_in_learning_activity"))
        focus = review_focus(candidate, lab, learning)
        implications = page_implications(candidate, lab, learning)

        reason_parts = [
            f"Page {page} includes {candidate['technology']} in surrounding instructional text."
        ]
        if lab:
            reason_parts.append(
                "The context appears connected to a lab, build task, exercise, or hands-on workflow."
            )
        if learning:
            reason_parts.append(
                "The context is near learning outcome, assessment, or student activity language."
            )
        if candidate["lifecycle_risk"] >= 30:
            reason_parts.append(
                "The technology has a stronger lifecycle signal, so faculty may want to validate the support status and documentation used on that page."
            )

        reasons.append(
            {
                "page": page,
                "context_text": context_text,
                "reason": " ".join(reason_parts),
                "review_focus": focus,
                "implications": implications,
            }
        )

    return reasons


def build_explainability(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    breakdown = candidate["score_breakdown"]
    frequency = int(candidate["frequency"])
    pages = candidate["pages"]
    lifecycle_risk = int(candidate["lifecycle_risk"])

    return [
        {
            "factor": "Lifecycle",
            "points": breakdown["technology_lifecycle_risk"],
            "max_points": 40,
            "evidence": candidate["lifecycle_status"],
            "implication": lifecycle_implication(lifecycle_risk),
            "review_question": (
                "Is the page teaching this technology as a current practice, a legacy maintenance example, or a historical comparison?"
            ),
        },
        {
            "factor": "Frequency",
            "points": breakdown["frequency"],
            "max_points": 30,
            "evidence": f"Detected {frequency} time(s) across page(s) {pages}.",
            "implication": frequency_implication(frequency),
            "review_question": (
                "Does the number of mentions indicate a passing reference or a repeated instructional dependency?"
            ),
        },
        {
            "factor": "Labs",
            "points": breakdown["appears_in_labs"],
            "max_points": 20,
            "evidence": (
                "Detected near lab, exercise, project, build, or implementation language."
                if candidate["appears_in_labs"]
                else "No lab-oriented context was detected in the sampled sentences."
            ),
            "implication": lab_implication(candidate["appears_in_labs"]),
            "review_question": (
                "Would students need current tooling, installation steps, screenshots, or commands to complete this activity?"
            ),
        },
        {
            "factor": "Activities",
            "points": breakdown["appears_in_learning_activities"],
            "max_points": 10,
            "evidence": (
                "Detected near student activity, outcome, assessment, objective, or demonstration language."
                if candidate["appears_in_learning_activities"]
                else "No learning-activity context was detected in the sampled sentences."
            ),
            "implication": learning_activity_implication(
                candidate["appears_in_learning_activities"]
            ),
            "review_question": (
                "Does the page still measure the intended competency, or should the activity be reframed?"
            ),
        },
    ]


def build_specific_recommendations(
    candidate: dict[str, Any], page_review_reasons: list[dict[str, Any]]
) -> list[str]:
    technology = candidate["technology"]
    pages = ", ".join(str(page) for page in candidate["pages"])
    recommendations = [
        f"Review page(s) {pages} and decide whether {technology} should be taught as a current workflow, a legacy maintenance scenario, or a comparison point.",
    ]

    if candidate["lifecycle_risk"] >= 30:
        recommendations.append(
            f"Add a short faculty note or updated reference that clarifies {technology}'s current support status and points students to maintained documentation."
        )
    elif candidate["lifecycle_risk"] >= 15:
        recommendations.append(
            f"Validate the version, support window, and documentation links for {technology} before using the page in the next delivery."
        )
    else:
        recommendations.append(
            f"Keep {technology} if it supports the learning outcome, but verify that examples use current documentation and setup guidance."
        )

    if candidate["appears_in_labs"]:
        recommendations.append(
            "Check lab instructions, package names, commands, screenshots, and grading criteria for friction students may encounter during hands-on work."
        )
    if candidate["appears_in_learning_activities"]:
        recommendations.append(
            "Map the activity back to the course outcome and confirm whether the assessment should emphasize concepts, tool usage, migration awareness, or comparison with modern alternatives."
        )

    recommendations.append(category_recommendation(candidate))

    if page_review_reasons:
        recommendations.append(
            f"Use the sampled page context as evidence during faculty review rather than treating the score as an automatic decision."
        )

    return recommendations


def review_focus(candidate: dict[str, Any], lab: bool, learning: bool) -> str:
    if lab and learning:
        return "Hands-on activity and outcome alignment"
    if lab:
        return "Lab workflow, setup steps, commands, and assessment friction"
    if learning:
        return "Learning outcome or assessment alignment"
    if candidate["lifecycle_risk"] >= 30:
        return "Technology support status and reference accuracy"
    return "Reference relevance and instructional fit"


def page_implications(candidate: dict[str, Any], lab: bool, learning: bool) -> list[str]:
    implications = []
    if candidate["lifecycle_risk"] >= 30:
        implications.append(
            "Students may rely on documentation, examples, or packages whose support status should be verified by faculty."
        )
    elif candidate["lifecycle_risk"] >= 15:
        implications.append(
            "Version-specific instructions may need confirmation against current official guidance."
        )
    else:
        implications.append(
            "The technology appears broadly current, so review should focus on whether the page uses current practices and references."
        )
    if lab:
        implications.append(
            "Hands-on tasks can create student blockers when setup steps, dependencies, or screenshots no longer match current tooling."
        )
    if learning:
        implications.append(
            "Because the mention is near student activity or outcome language, changes may affect assessments or competency mapping."
        )
    return implications


def lifecycle_implication(lifecycle_risk: int) -> str:
    if lifecycle_risk >= 30:
        return (
            "A high lifecycle contribution suggests faculty should validate support status, security posture, official documentation, and whether the technology is being used intentionally."
        )
    if lifecycle_risk >= 15:
        return (
            "A moderate lifecycle contribution suggests version support and documentation should be checked before reuse."
        )
    return (
        "A low lifecycle contribution suggests the technology is not the main driver of priority; review should focus on instructional fit."
    )


def frequency_implication(frequency: int) -> str:
    if frequency >= 5:
        return (
            "Repeated mentions suggest the technology may be embedded across examples, activities, or explanations, increasing review scope."
        )
    if frequency >= 2:
        return (
            "Multiple mentions suggest faculty should check whether references are isolated or part of a broader instructional pattern."
        )
    return (
        "A single mention contributes lightly; the page is flagged mainly because of lifecycle or instructional context signals."
    )


def lab_implication(appears_in_labs: bool) -> str:
    if appears_in_labs:
        return (
            "Lab context increases priority because students may need to install, configure, build, or submit work using the detected technology."
        )
    return (
        "Without lab context, the review impact may be limited to examples, references, or explanatory text."
    )


def learning_activity_implication(appears_in_learning_activities: bool) -> str:
    if appears_in_learning_activities:
        return (
            "Activity context increases priority because revisions could affect outcomes, rubrics, or assessment expectations."
        )
    return (
        "Without activity context, faculty can usually review the reference without changing the assessment design."
    )


def category_recommendation(candidate: dict[str, Any]) -> str:
    technology = candidate["technology"]
    category = candidate["category"].lower()

    if "frontend" in category:
        return (
            f"Compare the {technology} example with current frontend documentation, accessibility expectations, dependency setup, and component architecture used in industry."
        )
    if "css" in category:
        return (
            f"Check whether {technology} examples rely on layout classes, browser assumptions, or accessibility patterns that differ from current Bootstrap guidance."
        )
    if "runtime" in category:
        return (
            f"Confirm whether {technology} syntax, security assumptions, and server setup remain suitable for the intended backend competency."
        )
    if "version control" in category:
        return (
            f"Clarify whether {technology} is included to teach a specific workflow, to compare version control models, or to prepare students for current team practices."
        )
    if "database" in category:
        return (
            f"Validate {technology} examples against current SQL dialect guidance, connector setup, and deployment assumptions."
        )
    if "container" in category:
        return (
            f"Check whether {technology} instructions still match current image build, compose, registry, and deployment practices."
        )
    if "cloud" in category:
        return (
            f"Verify that {technology} examples use current service names, pricing-sensitive steps, and official learning paths."
        )
    if "ci/cd" in category:
        return (
            f"Review {technology} pipeline examples for plugin, credential, and workflow assumptions that may affect student labs."
        )
    return (
        f"Confirm that {technology} is still the right example for the learning outcome and update references if faculty decide to retain it."
    )
