import asyncio
from dotenv import load_dotenv
load_dotenv() # Load variables from .env first

from app.services.agentic_pipeline import build_review_report_agentic
from app.services.openai_review import analyze_candidate

async def main():
    print("Testing Agentic Pipeline Fallback Logic...")
    pages = [
        {"page": 1, "text": "This module covers Python and JavaScript. It's a great intro.", "images": []}
    ]
    try:
        report = build_review_report_agentic(pages, filename="test.pdf", file_size=100)
        print("Pipeline Success!")
    except Exception as e:
        print(f"Pipeline Failed with exception: {repr(e)}")

    print("\nTesting OpenAI Review Fallback Logic...")
    candidate = {
        "technology": "Python",
        "review_priority": "Low",
        "lifecycle_status": "Current",
        "pages": [1],
        "frequency": 1,
        "priority_score": 10,
        "sample_contexts": [{"page": 1, "text": "using python"}],
        "current_technology_references": [],
        "new_technology_references": [],
        "score_breakdown": {
            "technology_lifecycle_risk": 0,
            "frequency": 5,
            "appears_in_labs": 3,
            "appears_in_learning_activities": 2
        }
    }
    try:
        recommendation = analyze_candidate(candidate)
        print("Analyze Candidate Success!")
        print("Final AI Provider Used:", recommendation.get("ai_mode"))
    except Exception as e:
        print(f"Analyze Candidate Failed with exception: {repr(e)}")

if __name__ == "__main__":
    asyncio.run(main())
