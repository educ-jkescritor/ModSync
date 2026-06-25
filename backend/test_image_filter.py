import fitz
import sys
from PIL import Image
import io

def analyze_pdf_images(pdf_path):
    print(f"Analyzing {pdf_path}...")
    try:
        with fitz.open(pdf_path) as doc:
            for i, page in enumerate(doc):
                images = page.get_images(full=True)
                if images:
                    print(f"\n--- Page {i+1} ---")
                for img_idx, img in enumerate(images):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    ext = base_image["ext"]
                    
                    try:
                        pil_img = Image.open(io.BytesIO(image_bytes))
                        width, height = pil_img.size
                        
                        # Calculate color variance/extremes
                        extrema = pil_img.convert("L").getextrema()
                        # getextrema returns (min, max) pixel values
                        # If min == max, it's a solid color.
                        
                        is_solid = False
                        if extrema[0] == extrema[1]:
                            is_solid = True
                        
                        print(f"  Image {img_idx+1}: {width}x{height}, format: {ext}, solid color: {is_solid}, bytes: {len(image_bytes)}")
                    except Exception as e:
                        print(f"  Image {img_idx+1}: Could not analyze with PIL ({e})")
    except Exception as e:
        print(f"Failed to process PDF: {e}")

if __name__ == "__main__":
    pdf_path = r"C:\Users\Jude Keith Escritor\Downloads\Main PDF 7 - PHP Application with MySQL.pdf"
    analyze_pdf_images(pdf_path)
