import json
import os
import base64
from typing import Any
from openai import OpenAI
from google import genai
from google.genai import types

def build_review_report_agentic(pages: list[dict[str, Any]], filename: str | None = None, file_size: int | None = None) -> dict[str, Any]:
    openai_key = os.environ.get("OPENAI_API_KEY")
    gemini_key = os.environ.get("GEMINI_API_KEY")
    
    if not openai_key and not gemini_key:
        raise ValueError("Neither OPENAI_API_KEY nor GEMINI_API_KEY is set. Please add at least one to your .env file.")
        
    openai_client = OpenAI(api_key=openai_key) if openai_key else None
    gemini_client = genai.Client(api_key=gemini_key) if gemini_key else None
    
    models_to_try = []
    if openai_key:
        models_to_try.extend(["gpt-4o-mini", "gpt-4o"])
    if gemini_key:
        models_to_try.extend(["gemini-3.1-flash-lite", "gemini-3.1-pro-preview", "gemini-3.5-flash", "gemini-2.5-flash"])
    
    candidate_pages = []
    
    # ==========================================
    # AGENT 1: The Fast Extraction Scout
    # ==========================================
    print(f"Starting Agent 1: Fast Text Scouting with fallback list: {models_to_try}")
    for page in pages:
        text = page.get("text", "")
        images = page.get("images", [])
        
        found_techs = []
        if text.strip():
            prompt = (
                "Extract all programming languages, frameworks, databases, and software tools from the text below. "
                "Return a JSON object with a single key 'technologies' containing an array of strings. If none are found, return {\"technologies\": []}.\n\n"
                f"Text:\n{text[:5000]}" # Cap text length just in case
            )
            last_error = None
            for model_name in models_to_try:
                try:
                    if model_name.startswith("gpt-"):
                        response = openai_client.chat.completions.create(
                            model=model_name,
                            messages=[{"role": "user", "content": prompt}],
                            response_format={"type": "json_object"},
                            temperature=0.1
                        )
                        content = response.choices[0].message.content or "{}"
                    else:
                        response = gemini_client.models.generate_content(
                            model=model_name,
                            contents=prompt,
                            config=types.GenerateContentConfig(
                                response_mime_type="application/json",
                                temperature=0.1
                            )
                        )
                        content = response.text or "{}"
                        
                    found_techs = json.loads(content).get("technologies", [])
                    print(f"  Page {page['page']} tech found: {found_techs} (via {model_name})")
                    last_error = None
                    break
                except Exception as e:
                    error_msg = str(e).lower()
                    print(f"  Model {model_name} failed with {error_msg}, trying next...")
                    last_error = e
                    continue
            
            if last_error:
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=429, 
                    detail=f"All models failed. Last error: {last_error}"
                )                
        
        if found_techs:
            candidate_pages.append({
                "page": page["page"],
                "text": text,
                "images": [],
                "techs": found_techs
            })

    # ==========================================
    # AGENT 2: The Deep Multimodal Analyst
    # ==========================================
    print(f"Starting Agent 2: Deep Analysis on {len(candidate_pages)} candidate pages...")
    recommendations = []
    
    if candidate_pages:
        system_prompt = (
            "You are an expert curriculum reviewer. Analyze the following text extracted from a module. "
            "Identify technologies, evaluate if they are outdated, and provide actionable recommendations. \n"
            "IMPORTANT SCORING RUBRIC:\n"
            "1. Calculate the 'priority_score' (0-100) strictly by adding the following sub-scores in 'score_breakdown':\n"
            "   - 'technology_lifecycle_risk' (MUST BE BETWEEN 0 AND 40 pts): Higher if tech is End-of-Life, deprecated, or completely dead.\n"
            "   - 'frequency' (MUST BE BETWEEN 0 AND 30 pts): Higher if the technology appears heavily across the module.\n"
            "   - 'appears_in_labs' (MUST BE BETWEEN 0 AND 20 pts): Higher if students use it in hands-on labs.\n"
            "   - 'appears_in_learning_activities' (MUST BE BETWEEN 0 AND 10 pts): Higher if tied to learning outcomes/rubrics.\n"
            "2. Set the 'review_priority' using these strict thresholds: 80-100='High', 50-79='Medium', 0-49='Low'.\n"
            "3. Assign a 'confidence_score' (0.0-1.0) based solely on your certainty of the textual evidence.\n"
            "4. For 'current_technology_references', provide documentation and tutorials for the specific technology found. For 'new_technology_references', provide links for the recommended modern replacement (if applicable, else modern best practices).\n"
            "5. MIGRATION ASSISTANT: If the technology is outdated (Medium/High priority), you MUST generate a 'migration_guide' explaining how to modernize it. Also generate 'migration_legacy_code' showing the old context snippet, and 'migration_modern_code' showing the exact modern equivalent. Finally, provide 'migration_rationale_why_deprecated' and 'migration_rationale_modern_benefits'. If not outdated, you may leave these fields blank.\n"
            "Output a JSON object with a single key 'recommendations' containing an array of Recommendation objects matching the following JSON schema:\n"
            "{\n"
            "  \"type\": \"array\",\n"
            "  \"items\": {\n"
            "    \"type\": \"object\",\n"
            "    \"properties\": {\n"
            "      \"technology\": {\"type\": \"string\"},\n"
            "      \"review_priority\": {\"type\": \"string\", \"enum\": [\"High\", \"Medium\", \"Low\"]},\n"
            "      \"priority_score\": {\"type\": \"integer\"},\n"
            "      \"confidence_score\": {\"type\": \"number\"},\n"
            "      \"industry_observation\": {\"type\": \"string\"},\n"
            "      \"why_suggested\": {\"type\": \"string\"},\n"
            "      \"priority_rationale\": {\"type\": \"string\"},\n"
            "      \"suggested_faculty_action\": {\"type\": \"string\"},\n"
            "      \"specific_recommendations\": {\"type\": \"array\", \"items\": {\"type\": \"string\"}},\n"
            "      \"current_technology_references\": {\"type\": \"array\", \"items\": {\"type\": \"string\"}},\n"
            "      \"new_technology_references\": {\"type\": \"array\", \"items\": {\"type\": \"string\"}},\n"
            "      \"faculty_validation_required\": {\"type\": \"boolean\"},\n"
            "      \"score_breakdown\": {\n"
            "        \"type\": \"object\",\n"
            "        \"properties\": {\n"
            "          \"technology_lifecycle_risk\": {\"type\": \"integer\", \"minimum\": 0, \"maximum\": 40},\n"
            "          \"frequency\": {\"type\": \"integer\", \"minimum\": 0, \"maximum\": 30},\n"
            "          \"appears_in_labs\": {\"type\": \"integer\", \"minimum\": 0, \"maximum\": 20},\n"
            "          \"appears_in_learning_activities\": {\"type\": \"integer\", \"minimum\": 0, \"maximum\": 10}\n"
            "        },\n"
            "        \"required\": [\"technology_lifecycle_risk\", \"frequency\", \"appears_in_labs\", \"appears_in_learning_activities\"]\n"
            "      },\n"
            "      \"pages\": {\"type\": \"array\", \"items\": {\"type\": \"integer\"}},\n"
            "      \"frequency\": {\"type\": \"integer\"},\n"
            "      \"ai_mode\": {\"type\": \"string\"},\n"
            "      \"migration_guide\": {\"type\": \"string\"},\n"
            "      \"migration_legacy_code\": {\"type\": \"string\"},\n"
            "      \"migration_modern_code\": {\"type\": \"string\"},\n"
            "      \"migration_rationale_why_deprecated\": {\"type\": \"string\"},\n"
            "      \"migration_rationale_modern_benefits\": {\"type\": \"string\"}\n"
            "    },\n"
            "    \"required\": [\"technology\", \"review_priority\", \"priority_score\", \"confidence_score\", \"industry_observation\", \"why_suggested\", \"suggested_faculty_action\", \"score_breakdown\", \"pages\", \"frequency\", \"ai_mode\"]\n"
            "  }\n"
            "}"
        )
        
        contents_text = ""
        openai_content_parts = []
        gemini_image_parts = []
        for cp in candidate_pages:
            contents_text += f"\n--- PAGE {cp['page']} ---\n"
            contents_text += f"Agent 1 identified these technologies: {', '.join(cp['techs']) if cp['techs'] else 'None'}\n"
            
            curr_idx = cp['page'] - 1
            prev_text = ""
            if curr_idx > 0 and curr_idx - 1 < len(pages):
                prev_text = pages[curr_idx - 1].get("text", "").strip()
                
            next_text = ""
            if curr_idx + 1 < len(pages):
                next_text = pages[curr_idx + 1].get("text", "").strip()
                
            if prev_text:
                contents_text += f"[Previous Context - Page {cp['page'] - 1} Text]:\n{prev_text[:2000]}\n"
                
            if cp['text']:
                contents_text += f"[Current Context - Page {cp['page']} Text]:\n{cp['text']}\n"
                
            if next_text:
                contents_text += f"[Next Context - Page {cp['page'] + 1} Text]:\n{next_text[:2000]}\n"
            
            for img_b64 in cp.get('images', []):
                try:
                    img_bytes = base64.b64decode(img_b64)
                    # For Gemini
                    gemini_image_parts.append(types.Part.from_bytes(data=img_bytes, mime_type='image/png'))
                    # For OpenAI
                    openai_content_parts.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}})
                except Exception as e:
                    print(f"Could not load image on page {cp['page']}: {e}")
                    
        last_error = None
        for model_name in models_to_try:
            try:
                if model_name.startswith("gpt-"):
                    # Build OpenAI user message payload
                    openai_user_content = [{"type": "text", "text": contents_text}] + openai_content_parts
                    
                    response = openai_client.chat.completions.create(
                        model=model_name,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": openai_user_content}
                        ],
                        response_format={"type": "json_object"},
                        temperature=0.2
                    )
                    content = response.choices[0].message.content or "{}"
                else:
                    # For Gemini, we combine system prompt and user prompt
                    gemini_prompt = [system_prompt + "\n\n" + contents_text] + gemini_image_parts
                    response = gemini_client.models.generate_content(
                        model=model_name,
                        contents=gemini_prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            temperature=0.2
                        )
                    )
                    content = response.text or "{}"

                parsed_json = json.loads(content)
                recommendations = parsed_json.get("recommendations", [])
                
                # Fallback if Gemini returned raw array despite prompt tweak
                if not recommendations and isinstance(parsed_json, list):
                    recommendations = parsed_json
                    
                # Programmatically enforce math accuracy
                for rec in recommendations:
                    breakdown = rec.get("score_breakdown", {})
                    total = (
                        breakdown.get("technology_lifecycle_risk", 0) +
                        breakdown.get("frequency", 0) +
                        breakdown.get("appears_in_labs", 0) +
                        breakdown.get("appears_in_learning_activities", 0)
                    )
                    # Cap total at 100 just in case
                    total = min(100, max(0, total))
                    rec["priority_score"] = total
                    
                    if total >= 80:
                        rec["review_priority"] = "High"
                    elif total >= 50:
                        rec["review_priority"] = "Medium"
                    else:
                        rec["review_priority"] = "Low"
                    
                    
                print(f"Agent 2 successful via {model_name}")
                last_error = None
                break
            except Exception as e:
                error_msg = str(e).lower()
                print(f"Agent 2 Model {model_name} failed with {error_msg}, trying next...")
                last_error = e
                continue
        
        if last_error:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=429, 
                detail=f"All models failed. Last error: {last_error}"
            )

    return {
        "filename": filename,
        "file_size": file_size,
        "pages_analyzed": len(pages),
        "detections": [],
        "recommendations": recommendations,
        "summary": {
            "technology_count": len(recommendations),
            "relevant_pages_count": len(candidate_pages),
            "high_priority_count": sum(1 for r in recommendations if r.get("review_priority") == "High"),
            "medium_priority_count": sum(1 for r in recommendations if r.get("review_priority") == "Medium"),
            "low_priority_count": sum(1 for r in recommendations if r.get("review_priority") == "Low"),
        },
    }
