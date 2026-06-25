from __future__ import annotations

import json
import sys
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = ROOT / "backend"
OUTPUTS = ROOT / "outputs"
FRONTEND_PUBLIC = ROOT / "frontend" / "public"

sys.path.insert(0, str(BACKEND_ROOT))

from app.services.pdf_parser import extract_pdf_pages  # noqa: E402
from app.services.report_pipeline import build_review_report  # noqa: E402


PAGE_TEXT = [
    [
        "Module 4: Client-Side Application Development",
        "This module introduces browser-based application patterns.",
        "Students will build a lab activity using AngularJS and Bootstrap 3.",
        "The activity asks students to compare the interface with React and Vue examples.",
        "Faculty review suggested: confirm whether the chosen examples still support the target competencies.",
    ],
    [
        "Module 7: Backend and Deployment Practices",
        "Students will configure PHP 5 examples that connect to MySQL.",
        "For deployment, learners will package the service with Docker.",
        "A learning activity asks students to document version control with SVN and Git.",
        "Faculty validation is required before any curriculum decision is made.",
    ],
]


def create_pdf(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(path), pagesize=letter)
    width, height = letter

    for page_lines in PAGE_TEXT:
        text_object = pdf.beginText(72, height - 72)
        text_object.setFont("Helvetica-Bold", 15)
        text_object.textLine(page_lines[0])
        text_object.moveCursor(0, 18)
        text_object.setFont("Helvetica", 11)
        for line in page_lines[1:]:
            text_object.textLine(line)
            text_object.moveCursor(0, 8)
        pdf.drawText(text_object)
        pdf.setFont("Helvetica", 9)
        pdf.drawString(72, 48, "Faculty Curriculum Review Assistant demo PDF")
        pdf.showPage()

    pdf.save()


def main() -> None:
    demo_pdf = OUTPUTS / "example-module.pdf"
    sample_json = OUTPUTS / "sample-review-output.json"
    frontend_json = FRONTEND_PUBLIC / "sample-review-output.json"

    create_pdf(demo_pdf)
    pages = extract_pdf_pages(demo_pdf)
    report = build_review_report(
        pages, filename=demo_pdf.name, file_size=demo_pdf.stat().st_size
    )

    sample_json.parent.mkdir(parents=True, exist_ok=True)
    FRONTEND_PUBLIC.mkdir(parents=True, exist_ok=True)
    sample_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    frontend_json.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Wrote {demo_pdf}")
    print(f"Wrote {sample_json}")
    print(f"Wrote {frontend_json}")


if __name__ == "__main__":
    main()

