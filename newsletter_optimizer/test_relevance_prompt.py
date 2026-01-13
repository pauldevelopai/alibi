import unittest

from newsletter_engine import (
    PromptConstructor,
    NewsletterPlan,
    NewsletterSection,
    RequiredInputCoverage,
    StyleProfile,
)


class RelevancePromptTests(unittest.TestCase):
    def setUp(self):
        self.pc = PromptConstructor()

        self.plan = NewsletterPlan(
            theme="AI contractors and data uploads",
            audience="test",
            purpose="",
            angle_choices=["contractor risks"],
            required_inputs_coverage=[],
            style_profile=StyleProfile(style_tokens=["conversational"]),
            sections=[NewsletterSection(id="main", name="Main", goal="", word_count=400, sources_needed_min=1, source_anchor_requirements=["outline"])],
            call_to_action="",
            fact_risk_flags=[],
            outline_text="Outline",
            target_length=400,
        )

        self.facts = [
            {"id": "f1", "text": "Contractors asked to upload real work", "source_title": "TechCrunch"}
        ]
        self.rag = [
            {"text": "Past piece about contractor data", "newsletter_title": "Contractor Data Risk"}
        ]
        self.outline_sources = [
            {"title": "Provided", "url": "http://example.com", "summary": "Provided summary"}
        ]

    def test_relevance_caps(self):
        brief = self.pc.build_relevance_brief(self.plan, self.facts, self.rag, self.outline_sources)
        past = [r for r in brief.selected_items if r.source_type == "past_newsletter"]
        kb = [r for r in brief.selected_items if r.source_type == "knowledge_base"]
        self.assertLessEqual(len(past), 5)
        self.assertLessEqual(len(kb), 4)

    def test_prompt_no_dump(self):
        # Build pack and prompt, ensure no repeated From: blocks and no long dumps
        brief = self.pc.build_relevance_brief(self.plan, self.facts, self.rag, self.outline_sources)
        pack = self.pc._build_retrieval_pack(self.facts, self.rag, brief, self.outline_sources)
        system_prompt, user_prompt, meta = self.pc.build_prompt(
            outline="Headline\n\n## Section\nPoint",
            target_length=400,
            outline_sources=self.outline_sources,
            style_metrics={},
            outline_struct={},
        )
        self.assertNotIn("From:", user_prompt[:2000])
        kb_items = [ex for ex in pack.excerpts if ex.source_type == "knowledge_base"]
        self.assertLessEqual(len(kb_items), 4)

    def test_anchor_diversity(self):
        brief = self.pc.build_relevance_brief(self.plan, self.facts, self.rag, self.outline_sources)
        pack = self.pc._build_retrieval_pack(self.facts, self.rag, brief, self.outline_sources)
        anchored = self.pc.generate_anchored_outline(self.plan, pack)
        for sec in anchored.sections:
            sources = set()
            for b in sec.bullets:
                for a in b.anchors:
                    ex = next((e for e in pack.excerpts if e.id == a), None)
                    if ex:
                        sources.add(ex.source_type)
            self.assertTrue("past_newsletter" in sources or "newsletter_bible" in sources)
            self.assertTrue("knowledge_base" in sources or "facts" in sources or "provided_source" in sources)


if __name__ == "__main__":
    unittest.main()
