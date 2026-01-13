import unittest

from newsletter_engine import (
    PromptConstructor,
    NewsletterPlan,
    NewsletterSection,
    RequiredInputCoverage,
    StyleProfile,
    RetrievalPack,
    RetrievalExcerpt,
)


class AnchoredOutlineTests(unittest.TestCase):
    def setUp(self):
        self.pc = PromptConstructor()

    def _plan(self):
        return NewsletterPlan(
            theme="Test",
            audience="Testers",
            purpose="Check anchored outline",
            angle_choices=["A"],
            required_inputs_coverage=[
                RequiredInputCoverage(input_type="outline", must_use=True, allocated_sections=["main"]),
            ],
            style_profile=StyleProfile(),
            sections=[
                NewsletterSection(
                    id="main",
                    name="Main",
                    goal="Explain main idea",
                    word_count=400,
                    sources_needed_min=1,
                    source_anchor_requirements=["outline"],
                )
            ],
            call_to_action="CTA",
            fact_risk_flags=[],
            outline_text="Outline text",
            target_length=500,
            provided_sources_count=0,
        )

    def _pack(self):
        return RetrievalPack(
            excerpts=[
                RetrievalExcerpt(id="E_1", text="fact1", source_type="knowledge_base"),
                RetrievalExcerpt(id="V_1", text="example1", source_type="past_newsletter"),
            ]
        )

    def test_bullets_have_anchors(self):
        plan = self._plan()
        pack = self._pack()
        anchored = self.pc.generate_anchored_outline(plan, pack)
        for sec in anchored.sections:
            self.assertTrue(sec.bullets, "Section should have bullets")
            for b in sec.bullets:
                self.assertTrue(b.anchors, "Bullet must have anchors")

    def test_section_ids_present(self):
        plan = self._plan()
        pack = self._pack()
        anchored = self.pc.generate_anchored_outline(plan, pack)
        ids = [s.section_id for s in anchored.sections]
        self.assertIn("main", ids)

    def test_anchors_reference_pack(self):
        plan = self._plan()
        pack = self._pack()
        anchored = self.pc.generate_anchored_outline(plan, pack)
        pack_ids = {ex.id for ex in pack.excerpts}
        for sec in anchored.sections:
            for b in sec.bullets:
                for a in b.anchors:
                    self.assertIn(a, pack_ids)


if __name__ == "__main__":
    unittest.main()
