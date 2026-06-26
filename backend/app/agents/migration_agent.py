from __future__ import annotations

import json
from pydantic import BaseModel, Field
from google.genai import types
from google.genai import Client

class MigrationGuideResponse(BaseModel):
    migration_guide: str = Field(description="Step-by-step markdown migration guide for the faculty.")
    legacy_example: str = Field(description="Code snippet, terminal command, or context showing the outdated or deprecated approach.")
    modern_example: str = Field(description="Code snippet, terminal command, or context showing the updated, modern equivalent approach.")
    why_deprecated: str = Field(description="Detailed explanation of why the legacy approach is outdated/deprecated/risky, referencing official guidelines/standards if applicable.")
    modern_benefits: str = Field(description="Detailed explanation of why the modern equivalent is superior (e.g. safety, performance, maintainability).")

MIGRATION_SYSTEM_PROMPT = """You are ModSync's Migration Assistant Agent.
Your job is to provide concrete, highly practical technical guidance for transitioning or migrating from an outdated, deprecated, or superseded technology, standard, medical guideline, law, theory, or formula to its modern counterpart.

Given a concept name, its status, and a suggested action:
1. Draft a step-by-step transition/migration guide (2-3 concise steps in markdown).
2. Write a brief "legacy" code snippet, terminal command, old formula, outdated guideline text, or instruction showing the deprecated/old way.
3. Write a brief "modern" code snippet, terminal command, new formula, updated guideline text, or instruction showing the modern/current standard way.
4. Explain WHY the legacy approach is deprecated (technical risks, EOL, readability, standards bodies like ISO or MISRA).
5. Explain WHY the modern approach is better (readability, compile-time checks, security, community support).

Return the result as JSON matching the requested schema.
"""

def generate_migration_plan(
    client: Client,
    model: str,
    technology: str,
    status: str,
    suggested_action: str
) -> MigrationGuideResponse:
    """Generates side-by-side migration code examples and step-by-step markdown instructions."""
    user_prompt = f"Technology: {technology}\nStatus: {status}\nSuggested Action: {suggested_action}"
    
    try:
        from ..services.gemini_client import generate_content_with_retry
        response = generate_content_with_retry(
            client=client,
            model=model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=MIGRATION_SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=MigrationGuideResponse,
                temperature=0.1
            )
        )
        if response.text:
            return MigrationGuideResponse.model_validate(json.loads(response.text))
    except Exception as exc:
        print(f"Error in Migration Agent for {technology}: {exc}")
        
    return MigrationGuideResponse(
        migration_guide=f"1. Evaluate use of {technology} in labs.\n2. Consult current best practices to transition.",
        legacy_example=f"# Outdated usage of {technology}",
        modern_example="# Modern equivalent approach",
        why_deprecated=f"The use of {technology} is outdated and does not align with current security and maintainability standards.",
        modern_benefits="The modern alternative provides active support, safety improvements, and cleaner structure."
    )
