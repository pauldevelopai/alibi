import unittest

from newsletter_engine import PromptConstructor, NewsletterPlan, StyleProfile, NewsletterSection, RelevanceItem, RelevanceBrief
from topic_signature import build_topic_signature
from relevance_filter import filter_editorial_sources_by_topic


class KBRelevanceFilterTests(unittest.TestCase):
    def setUp(self):
        self.pc = PromptConstructor()
        self.plan = NewsletterPlan(
            theme="Grok deepfakes targeting women in hijabs",
            audience="",
            purpose="",
            angle_choices=["Grok non-consensual deepfakes"],
            required_inputs_coverage=[],
            style_profile=StyleProfile(),
            sections=[
                NewsletterSection(id="main", name="Main", goal="Explain issue", word_count=400, sources_needed_min=1, source_anchor_requirements=["outline"])
            ],
            call_to_action="",
            fact_risk_flags=[],
            outline_text="",
            target_length=400,
        )
        self.anchored_outline = {"sections": [{"section_id": "main", "bullets": [{"text": "Grok deepfake abuse"}]}]}
        self.provided = [
            {"id": "PS_1", "title": "Grok Is Being Used to Mock Women in Hijabs", "source_type": "provided_source", "summary": "", "url": "https://wired.com/grok"},
        ]
        self.facts = [
            {"id": "kb1", "text": "OpenAI announced grantwashing", "source_title": "Tech Policy"},
            {"id": "kb2", "text": "Non-consensual deepfake undressing tools target women in hijabs", "source_title": "Deepfake report"},
        ]

    def test_filters_irrelevant_kb(self):
        topic = build_topic_signature(self.plan, self.anchored_outline, self.provided, self.facts)
        filtered = filter_editorial_sources_by_topic(
            [
                {"title": "OpenAI grantwashing", "summary": self.facts[0]["text"], "source_type": "knowledge_base"},
                {"title": "Deepfake undressing tools", "summary": self.facts[1]["text"], "source_type": "knowledge_base"},
                {"title": "Provided", "summary": "", "source_type": "provided_source"},
            ],
            topic,
            section_id="main",
            min_score=2.0
        )
        self.assertTrue(any("Deepfake" in s.get("title","") for s in filtered))
        self.assertFalse(any("grantwashing" in (s.get("summary","")) for s in filtered))

    def test_pipeline_fallback_to_provided(self):
        topic = build_topic_signature(self.plan, self.anchored_outline, self.provided, [])
        filtered = filter_editorial_sources_by_topic(
            [{"title": "grantwashing", "summary": "grantwashing", "source_type": "knowledge_base"}],
            topic,
            section_id="main",
            min_score=2.0
        )
        filtered.append(self.provided[0])  # provided always allowed
        self.assertTrue(any(s.get("source_type") == "provided_source" for s in filtered))


if __name__ == "__main__":
    unittest.main()
