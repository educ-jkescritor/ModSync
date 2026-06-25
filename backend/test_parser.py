from app.services.pdf_parser import extract_pdf_pages
import sys

def test():
    print("Testing PDF extraction...")
    try:
        pages = extract_pdf_pages("../outputs/example-module.pdf")
        for p in pages:
            text_preview = p['text'][:50].replace('\n', ' ') + "..." if p['text'] else "No text"
            num_images = len(p.get("images", []))
            
            print(f"\n--- Page {p['page']} ---")
            print(f"Text length: {len(p['text'])} characters")
            print(f"Text preview: {text_preview}")
            print(f"Images found: {num_images}")
            
            if num_images > 0:
                print(f"First image base64 length: {len(p['images'][0])} characters")
                
        print("\nExtraction test completed successfully!")
    except Exception as e:
        print(f"Error during extraction: {e}")

if __name__ == "__main__":
    test()
