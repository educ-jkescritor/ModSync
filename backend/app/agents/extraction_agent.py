from __future__ import annotations

import json
from typing import List, Optional
from pydantic import BaseModel, Field
from google.genai import types
from google.genai import Client

class Concept(BaseModel):
    name: str = Field(description="Name of the technology, standard, theory, framework, law, or terminology.")
    role: str = Field(description="The instructional role (e.g. Learning Objective, Main Topic, Laboratory Activity, Assessment, Example, Historical Context).")
    evidence: str = Field(description="Exact quote or visual evidence from the page indicating how the concept is used.")

class ExtractedImage(BaseModel):
    description: str = Field(description="Visual description of the diagram, screenshot, table, image, chart, or figure.")
    purpose: str = Field(description="The educational or instructional purpose of this image/diagram.")

class PageExtraction(BaseModel):
    page: int = Field(description="The page number.")
    subject: str = Field(description="The subject area (e.g. Computer Science, Nursing, Philosophy, Law, etc.).")
    concepts: List[Concept] = Field(default_factory=list, description="List of all concepts detected on this page.")
    images: List[ExtractedImage] = Field(default_factory=list, description="List of all visual elements detected on this page.")

EXTRACTION_SYSTEM_PROMPT = """You are ModSync's Multimodal Extraction Agent.
Analyze this educational module page visually and semantically.

Extract:
1. Subject area (e.g. Computer Science, Nursing, Philosophy, etc.).
2. Learning objectives listed on this page.
3. Main concepts discussed.
4. Technologies, frameworks, standards, laws, theories, formulas, methodologies, and terminologies.
5. Activities, exercises, assessments, and laboratory instructions.
6. Visual information from diagrams, screenshots, tables, images, charts, and figures.
7. Determine how each concept is used:
   - Learning Objective
   - Main Topic
   - Laboratory Activity
   - Assessment
   - Example
   - Historical Context
8. Include exact page evidence/quotes.

Return the result as JSON matching the requested schema.
"""

def extract_page_contents(
    client: Client,
    model: str,
    page_num: int,
    image_bytes: bytes
) -> PageExtraction:
    """Uses Gemini vision to extract text and visual concepts from a PDF page image."""
    try:
        from ..services.gemini_client import generate_content_with_retry
        response = generate_content_with_retry(
            client=client,
            model=model,
            contents=[
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type="image/png"
                ),
                f"Analyze page {page_num} of this educational module."
            ],
            config=types.GenerateContentConfig(
                system_instruction=EXTRACTION_SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=PageExtraction,
                temperature=0.1
            )
        )
        # Parse output into Pydantic model
        if response.text:
            data = json.loads(response.text)
            data["page"] = page_num  # Enforce page number
            return PageExtraction.model_validate(data)
        else:
            return PageExtraction(page=page_num, subject="Unknown")
    except Exception as exc:
        print(f"Error in Multimodal Extraction Agent for page {page_num}: {exc}")
        # Return empty page extraction in case of error
        return PageExtraction(page=page_num, subject="Error")
