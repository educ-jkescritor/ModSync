import os
from dotenv import load_dotenv

load_dotenv()

from app.services.pdf_parser import extract_pdf_pages
from app.services.agentic_pipeline import build_review_report_agentic
import json

def test():
    print("=== Testing the Agentic Pipeline ===")
    pdf_path = "../outputs/example-module.pdf"
    
    print(f"Extracting pages from {pdf_path}...")
    pages = extract_pdf_pages(pdf_path)
    print(f"Extracted {len(pages)} pages.")
    
    print("\nRunning Agentic Pipeline...")
    try:
        report = build_review_report_agentic(pages, filename="example-module.pdf", file_size=1000)
        print("\n=== Pipeline Succeeded! ===")
        print("Summary:")
        print(json.dumps(report["summary"], indent=2))
        
        if report["recommendations"]:
            print("\nFirst Recommendation Found:")
            print(f"  Technology: {report['recommendations'][0]['technology']}")
            print(f"  Priority: {report['recommendations'][0]['review_priority']}")
            print(f"  Pages: {report['recommendations'][0].get('pages', [])}")
        else:
            print("\nNo recommendations found (this could be normal if no outdated tech exists).")
    except Exception as e:
        import traceback
        print(f"\n=== Pipeline Failed ===")
        traceback.print_exc()

if __name__ == "__main__":
    test()
