from __future__ import annotations

import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.context_extraction import extract_contexts
from app.services.language_guardrails import (
    BLOCKED_CONTENT_LABEL,
    BLOCKED_CURRICULUM_LABEL,
    BLOCKED_REVIEW_LABEL,
)
from app.services.language_guardrails import apply_language_guardrails
from app.services.metadata_builder import build_metadata
from app.services.report_pipeline import build_review_report
from app.services.scoring import score_candidates
from app.services.technology_detection import detect_technologies


SAMPLE_PAGES = [
    {
        "page": 1,
        "text": (
            "This module introduces client-side development. "
            "Students will build a lab activity using AngularJS and Bootstrap 3. "
            "The next lesson compares React and Vue patterns."
        ),
    },
    {
        "page": 2,
        "text": (
            "For deployment, learners will use Docker. "
            "Students will document the workflow with Git. "
            "A final exercise asks students to describe SVN workflows."
        ),
    },
]


class ServicePipelineTests(unittest.TestCase):
    def test_detection_finds_known_technologies(self) -> None:
        detections = detect_technologies(SAMPLE_PAGES)
        technologies = {item["technology"] for item in detections}

        self.assertIn("AngularJS", technologies)
        self.assertIn("Bootstrap 3", technologies)
        self.assertIn("Docker", technologies)

    def test_context_window_is_limited_to_three_sentences(self) -> None:
        detections = detect_technologies(SAMPLE_PAGES)
        contexts = extract_contexts(SAMPLE_PAGES, detections)
        angular_context = next(item for item in contexts if item["technology"] == "AngularJS")

        self.assertLessEqual(len(angular_context["context"]), 3)
        self.assertTrue(angular_context["appears_in_lab"])
        self.assertTrue(angular_context["appears_in_learning_activity"])

    def test_scoring_prioritizes_high_risk_lab_content(self) -> None:
        detections = detect_technologies(SAMPLE_PAGES)
        contexts = extract_contexts(SAMPLE_PAGES, detections)
        metadata = build_metadata(detections, contexts)
        candidates = score_candidates(metadata)
        angular = next(item for item in candidates if item["technology"] == "AngularJS")

        self.assertEqual(angular["review_priority"], "High")
        self.assertGreaterEqual(angular["priority_score"], 75)

    def test_report_uses_review_recommendation_language(self) -> None:
        report = build_review_report(SAMPLE_PAGES, filename="sample.pdf", file_size=100)
        rendered = str(report).lower()

        self.assertIn("faculty_validation_required", rendered)
        self.assertNotIn(BLOCKED_REVIEW_LABEL, rendered)
        self.assertNotIn(BLOCKED_CURRICULUM_LABEL, rendered)
        self.assertNotIn(BLOCKED_CONTENT_LABEL, rendered)

    def test_report_includes_explainability_and_specific_actions(self) -> None:
        report = build_review_report(SAMPLE_PAGES, filename="sample.pdf", file_size=100)
        angular = next(
            item for item in report["recommendations"] if item["technology"] == "AngularJS"
        )

        self.assertIn("priority_rationale", angular)
        self.assertIn("specific_recommendations", angular)
        self.assertIn("page_review_reasons", angular)
        self.assertIn("explainability", angular)
        self.assertGreater(len(angular["specific_recommendations"]), 2)
        self.assertEqual(
            {item["factor"] for item in angular["explainability"]},
            {"Lifecycle", "Frequency", "Labs", "Activities"},
        )
        self.assertEqual(angular["page_review_reasons"][0]["page"], 1)
        self.assertIn("Hands-on", angular["page_review_reasons"][0]["review_focus"])

    def test_language_guardrails_replace_blocked_phrases(self) -> None:
        guarded = apply_language_guardrails({"text": f"This is an {BLOCKED_REVIEW_LABEL}."})

        self.assertNotIn(BLOCKED_REVIEW_LABEL, guarded["text"])
        self.assertIn("may warrant review", guarded["text"])


if __name__ == "__main__":
    unittest.main()
