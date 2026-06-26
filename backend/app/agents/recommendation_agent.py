from __future__ import annotations

import json
from typing import List
from pydantic import BaseModel, Field
from google.genai import types
from google.genai import Client

class PageReviewReason(BaseModel):
    page: int = Field(description="The page number.")
    context_text: str = Field(description="The quote or context from the page.")
    reason: str = Field(description="AI explanation of why this page is flagged and what needs review. Keep to 1-2 sentences.")
    review_focus: str = Field(description="The area of focus for the review on this page (e.g. Lab instructions update, Course outcome mapping).")
    implications: List[str] = Field(description="List of student or curriculum implications (e.g. 'Students may face installation issues').")

class RecommendationItem(BaseModel):
    technology: str = Field(description="Name of the technology/concept.")
    review_priority: str = Field(description="Priority level: 'High', 'Medium', or 'Low'.")
    priority_score: int = Field(description="Priority score between 0 and 100.")
    confidence_score: float = Field(description="Confidence score of this recommendation (0.0 to 1.0).")
    industry_observation: str = Field(description="What the industry currently uses, standard alternatives, or modern practices. Keep to 1-2 concise sentences.")
    why_suggested: str = Field(description="Why this is flagged, linking to how it's taught in the module. Keep to 1-2 concise sentences.")
    priority_rationale: str = Field(description="Explanation of how the lifecycle risk and instructional role justify the priority level. Keep to 1-2 concise sentences.")
    suggested_faculty_action: str = Field(description="A highly practical, actionable recommendation for faculty. Keep to 1-2 concise sentences.")
    specific_recommendations: List[str] = Field(description="Step-by-step practical suggestions for updating the curriculum.")
    page_review_reasons: List[PageReviewReason] = Field(description="Page-level review reasons.")
    score_breakdown_lifecycle: int = Field(description="Lifecycle risk points (0 to 40).")
    score_breakdown_frequency: int = Field(description="Frequency points (0 to 30).")
    score_breakdown_labs: int = Field(description="Labs points (0 or 20).")
    score_breakdown_activities: int = Field(description="Activities points (0 or 10).")

class RecommendationResponse(BaseModel):
    recommendations: List[RecommendationItem] = Field(default_factory=list)

RECOMMENDATION_SYSTEM_PROMPT = """You are ModSync's Faculty Recommendation Agent.
Your job is to synthesize all extracted page context and validation results into actionable, evidence-based recommendations for university faculty.

For each concept, you must provide:
1. Priority Level ('High', 'Medium', or 'Low') and a priority score (0-100).
   The score breakdown should follow these guidelines:
   - Lifecycle Risk (0-40 points): Deprecated = 40, Historical only = 30, Legacy = 20, Current = 0.
   - Frequency (0-30 points): 6 points per page mention, up to 30.
   - Labs (0 or 20 points): 20 points if it is taught in a hands-on laboratory or programming exercise, otherwise 0.
   - Activities (0 or 10 points): 10 points if it appears in learning objectives, assessments, or outcomes, otherwise 0.
2. Industry Observation (1-2 concise sentences): What industry is using as standard alternatives.
3. Why Suggested (1-2 concise sentences): Explaining why this is flagged in relation to how it is taught.
4. Priority Rationale (1-2 concise sentences): Explaining why it received this priority score.
5. Suggested Faculty Action (1-2 concise sentences): Highly practical first step.
6. Specific Recommendations: Bullet points of actionable steps.
7. Page Review Reasons: Breakdown of what needs to be reviewed on each page it was found.

Rules:
- Faculty members are the final decision-makers; write respectfully as an advisor.
- Keep all texts (why_suggested, industry_observation, suggested_faculty_action, priority_rationale) extremely concise (1-2 direct sentences max).
- Return the result as JSON matching the requested schema.
"""

def generate_recommendations(
    client: Client,
    model: str,
    extractions: list[dict],
    validations: list[dict]
) -> RecommendationResponse:
    """Synthesizes page extractions and validation details into complete recommendations."""
    if not extractions or not validations:
        return RecommendationResponse(recommendations=[])

    input_data = {
        "extractions": extractions,
        "validations": validations
    }

    user_prompt = f"Synthesize recommendations for the following inputs:\n{json.dumps(input_data, indent=2)}"

    try:
        from ..services.gemini_client import generate_content_with_retry
        response = generate_content_with_retry(
            client=client,
            model=model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=RECOMMENDATION_SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=RecommendationResponse,
                temperature=0.1
            )
        )
        if response.text:
            return RecommendationResponse.model_validate(json.loads(response.text))
    except Exception as exc:
        print(f"Error in Recommendation Agent: {exc}")

    return RecommendationResponse(recommendations=[])
