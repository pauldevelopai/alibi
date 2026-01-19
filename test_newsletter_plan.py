import unittest

from newsletter_engine import (
    PromptConstructor,
    RequiredInputCoverage,
    NewsletterSection,
    NewsletterPlan,
    StyleProfile,
)


class NewsletterPlanValidationTests(unittest.TestCase):
    def setUp(self):
        self.validator = PromptConstructor()._validate_newsletter_plan  # type: ignore

    def _plan(self, coverage, sections):
        return NewsletterPlan(
            theme="Test",
            audience="Testers",
            purpose="Check validation",
            angle_choices=["Angle A"],
            required_inputs_coverage=coverage,
            style_profile=StyleProfile(),
            sections=sections,
            call_to_action="Test CTA",
            fact_risk_flags=[],
            outline_text="Outline text",
            target_length=500,
            provided_sources_count=0,
        )

    def test_missing_required_input_coverage_fails(self):
        required = ["outline", "facts"]
        coverage = [
            RequiredInputCoverage(input_type="outline", must_use=True, allocated_sections=["main"])
        ]
        sections = [
            NewsletterSection(
                id="main", name="Main", goal="goal", word_count=400, sources_needed_min=1, source_anchor_requirements=["outline"]
            )
        ]
        plan = self._plan(coverage, sections)
        errors = self.validator(plan, required)
        self.assertTrue(any("facts" in e for e in errors))

    def test_section_without_anchor_fails(self):
        required = ["outline"]
        coverage = [RequiredInputCoverage(input_type="outline", must_use=True, allocated_sections=[])]
        sections = [
            NewsletterSection(
                id="main", name="Main", goal="goal", word_count=400, sources_needed_min=1, source_anchor_requirements=[]
            )
        ]
        plan = self._plan(coverage, sections)
        errors = self.validator(plan, required)
        self.assertTrue(any("Section" in e for e in errors))

    def test_valid_plan_passes(self):
        required = ["outline", "facts"]
        coverage = [
            RequiredInputCoverage(input_type="outline", must_use=True, allocated_sections=["main"]),
            RequiredInputCoverage(input_type="facts", must_use=True, allocated_sections=["main"]),
        ]
        sections = [
            NewsletterSection(
                id="main",
                name="Main",
                goal="goal",
                word_count=400,
                sources_needed_min=1,
                source_anchor_requirements=["outline", "facts"],
            )
        ]
        plan = self._plan(coverage, sections)
        errors = self.validator(plan, required)
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
