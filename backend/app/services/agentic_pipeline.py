import json
import os
import base64
from typing import Any
from google import genai
from google.genai import types

def build_review_report_agentic(pages: list[dict[str, Any]], filename: str | None = None, file_size: int | None = None) -> dict[str, Any]:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set. Please add it to your .env file.")
        
    client = genai.Client(api_key=api_key)
    
    candidate_pages = []
    
    # ==========================================
    # AGENT 1: The Fast Extraction Scout (Gemini 1.5 Flash)
    # ==========================================
    print("Starting Agent 1: Fast Text Scouting...")
    for page in pages:
        text = page.get("text", "")
        images = page.get("images", [])
        
        found_techs = []
        if text.strip():
            try:
                prompt = (
                    "Extract all programming languages, frameworks, databases, and software tools from the text below. "
                    "Return ONLY a JSON array of strings. If none are found, return [].\n\n"
                    f"Text:\n{text[:5000]}" # Cap text length just in case
                )
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.1
                    ),
                )
                found_techs = json.loads(response.text)
                if not isinstance(found_techs, list):
                    found_techs = []
                print(f"  Page {page['page']} tech found: {found_techs}")
            except Exception as e:
                error_msg = str(e).lower()
                if "429" in error_msg or "quota" in error_msg or "exhausted" in error_msg:
                    from fastapi import HTTPException
                    raise HTTPException(
                        status_code=429, 
                        detail="API Quota Reached: You have exceeded the free tier limit for the Gemini AI model. Please wait a minute and try again, or upgrade your plan."
                    )
                print(f"  Agent 1 skipped page {page['page']} due to error: {e}")
                
        # Text-only branch: Flag only if Agent 1 found text-based tech
        if found_techs:
            candidate_pages.append({
                "page": page["page"],
                "text": text,
                "images": [],
                "techs": found_techs
            })

    # ==========================================
    # AGENT 2: The Deep Multimodal Analyst (Gemini 1.5 Pro)
    # ==========================================
    print(f"Starting Agent 2: Deep Analysis on {len(candidate_pages)} candidate pages...")
    recommendations = []
    
    if candidate_pages:
        contents = [
            "You are an expert curriculum reviewer. Analyze the following text extracted from a module. "
            "Identify technologies, evaluate if they are outdated, and provide actionable recommendations. \n"
            "IMPORTANT SCORING RUBRIC:\n"
            "1. Calculate the 'priority_score' (0-100) strictly by adding the following sub-scores in 'score_breakdown':\n"
            "   - 'technology_lifecycle_risk' (0-40 pts): Higher if tech is End-of-Life, deprecated, or completely dead.\n"
            "   - 'frequency' (0-20 pts): Higher if the technology appears heavily across the module.\n"
            "   - 'appears_in_labs' + 'appears_in_learning_activities' (0-40 pts combined): Max points if students are actively graded or practicing it.\n"
            "2. Set the 'review_priority' using these strict thresholds: 80-100='High', 50-79='Medium', 0-49='Low'.\n"
            "3. Assign a 'confidence_score' (0.0-1.0) based solely on your certainty of the textual evidence.\n"
            "Output ONLY a JSON array of Recommendation objects matching the requested schema."
        ]
        
        for cp in candidate_pages:
            contents.append(f"--- PAGE {cp['page']} ---")
            contents.append(f"Agent 1 identified these technologies: {', '.join(cp['techs']) if cp['techs'] else 'None'}")
            
            # The Sliding Window (Gluer): Attach N-1 and N+1 text context
            curr_idx = cp['page'] - 1 # page numbers are 1-indexed, list is 0-indexed
            
            prev_text = ""
            if curr_idx > 0 and curr_idx - 1 < len(pages):
                prev_text = pages[curr_idx - 1].get("text", "").strip()
                
            next_text = ""
            if curr_idx + 1 < len(pages):
                next_text = pages[curr_idx + 1].get("text", "").strip()
                
            if prev_text:
                contents.append(f"[Previous Context - Page {cp['page'] - 1} Text]:\n{prev_text[:2000]}") # Cap length
                
            if cp['text']:
                contents.append(f"[Current Context - Page {cp['page']} Text]:\n{cp['text']}")
                
            if next_text:
                contents.append(f"[Next Context - Page {cp['page'] + 1} Text]:\n{next_text[:2000]}") # Cap length
            
            # Image loading removed for text-only safety branch
                    
        # Define the strict JSON schema that matches our React Frontend
        schema = {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "technology": {"type": "STRING"},
                    "review_priority": {"type": "STRING", "enum": ["High", "Medium", "Low"]},
                    "priority_score": {"type": "INTEGER"},
                    "confidence_score": {"type": "NUMBER"},
                    "industry_observation": {"type": "STRING"},
                    "why_suggested": {"type": "STRING"},
                    "priority_rationale": {"type": "STRING"},
                    "suggested_faculty_action": {"type": "STRING"},
                    "specific_recommendations": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "official_documentation": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "learning_resources": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "faculty_validation_required": {"type": "BOOLEAN"},
                    "score_breakdown": {
                        "type": "OBJECT",
                        "properties": {
                            "technology_lifecycle_risk": {"type": "INTEGER"},
                            "frequency": {"type": "INTEGER"},
                            "appears_in_labs": {"type": "INTEGER"},
                            "appears_in_learning_activities": {"type": "INTEGER"}
                        }
                    },
                    "pages": {"type": "ARRAY", "items": {"type": "INTEGER"}},
                    "frequency": {"type": "INTEGER"},
                    "ai_mode": {"type": "STRING"}
                },
                "required": ["technology", "review_priority", "priority_score", "confidence_score", "industry_observation", "why_suggested", "suggested_faculty_action", "score_breakdown", "pages", "frequency", "ai_mode"]
            }
        }
        
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=contents,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=schema,
                    temperature=0.2
                ),
            )
            recommendations = json.loads(response.text)
        except Exception as e:
            error_msg = str(e).lower()
            if "429" in error_msg or "quota" in error_msg or "exhausted" in error_msg:
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=429, 
                    detail="API Quota Reached: You have exceeded the free tier limit for the Gemini AI model. Please wait a minute and try again, or upgrade your plan."
                )
            print(f"Agent 2 error: {e}")
            raise ValueError(f"Agent 2 failed to generate report: {e}")

    # Return the exact dictionary format the frontend expects
    return {
        "filename": filename,
        "file_size": file_size,
        "pages_analyzed": len(pages),
        "recommendations": recommendations,
        "summary": {
            "technology_count": len(recommendations),
            "review_candidate_count": len(recommendations),
            "high_priority_count": sum(1 for r in recommendations if r.get("review_priority") == "High"),
            "medium_priority_count": sum(1 for r in recommendations if r.get("review_priority") == "Medium"),
            "low_priority_count": sum(1 for r in recommendations if r.get("review_priority") == "Low"),
        },
    }
