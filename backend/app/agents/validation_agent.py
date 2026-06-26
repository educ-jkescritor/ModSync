from __future__ import annotations

import json
from typing import List
from pydantic import BaseModel, Field
from google.genai import types
from google.genai import Client

class ValidationItem(BaseModel):
    concept: str = Field(description="Name of the concept.")
    status: str = Field(description="Academic and industry status (e.g. Current, Legacy but still useful, Historical only, Deprecated).")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0.")
    reason: str = Field(description="Reasoning about why this status was assigned, citing dates or support status where appropriate. Keep it to 1-2 concise sentences.")
    official_documentation: List[str] = Field(default_factory=list, description="Valid URLs to official documentation or announcements.")
    learning_resources: List[str] = Field(default_factory=list, description="Valid URLs to tutorial, migration guides, or academic resources.")

class ValidationResponse(BaseModel):
    validations: List[ValidationItem] = Field(default_factory=list)

VALIDATION_SYSTEM_PROMPT = """You are ModSync's Validation and Evidence Agent.
Given a list of extracted concepts from an educational course module:

1. Determine whether each concept remains academically and industrially valid, or if it is outdated, deprecated, legacy, or superseded.
2. Classify its status:
   - 'Current' (widely used in industry or current standard)
   - 'Legacy but still useful' (being phased out but still taught for maintenance or context)
   - 'Historical only' (no longer in practical use, only useful for historical comparison)
   - 'Deprecated' (officially reaching End-of-Life, unsupported, or superseded by a newer version/standard)
3. Explain why, including details like official End-of-Life dates or newer standard names. Keep this explanation extremely brief (1-2 sentences).
4. Provide a confidence score (0.0 to 1.0).
5. Retrieve or provide 1-2 high-quality URLs for official documentation (e.g., official site, EOL announcement) and 1-2 learning/migration resources.

Return the result as JSON matching the requested schema.
"""

def validate_concepts(
    client: Client,
    model: str,
    concepts_to_validate: list[dict]
) -> ValidationResponse:
    """Validates the extracted concepts against industry standards and retrieves references using Gemini Search Grounding."""
    if not concepts_to_validate:
        return ValidationResponse(validations=[])

    user_prompt = f"Validate the following concepts:\n{json.dumps(concepts_to_validate, indent=2)}"

    from ..services.gemini_client import generate_content_with_retry
    # Try calling with Google Search grounding first
    try:
        response = generate_content_with_retry(
            client=client,
            model=model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=VALIDATION_SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=ValidationResponse,
                temperature=0.1,
                tools=[types.Tool(google_search=types.GoogleSearch())]
            )
        )
        if response.text:
            return ValidationResponse.model_validate(json.loads(response.text))
    except Exception as exc:
        print(f"Warning: Failed to validate concepts with Search Grounding: {exc}. Retrying without search tool...")
        
    # Fallback to no tools if search grounding fails
    try:
        response = generate_content_with_retry(
            client=client,
            model=model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=VALIDATION_SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=ValidationResponse,
                temperature=0.1
            )
        )
        if response.text:
            return ValidationResponse.model_validate(json.loads(response.text))
    except Exception as exc:
        print(f"Error in Validation Agent: {exc}")
        
    # Return basic default validations as fallback
    fallback_items = []
    for item in concepts_to_validate:
        fallback_items.append(
            ValidationItem(
                concept=item.get("name", "Unknown"),
                status="Current",
                confidence=0.5,
                reason="Verification fallback - could not reach validation service.",
                official_documentation=[],
                learning_resources=[]
            )
        )
    return ValidationResponse(validations=fallback_items)
