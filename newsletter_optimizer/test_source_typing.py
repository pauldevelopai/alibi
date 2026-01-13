import unittest

from newsletter_engine import PromptConstructor, SourceType


class SourceTypingTests(unittest.TestCase):
    def setUp(self):
        self.pc = PromptConstructor()

    def test_marketing_filtered(self):
        srcs = [
            {"title": "Sign up now", "summary": "Subscribe for $5", "url": "http://example.com"},
            {"title": "Report", "summary": "Analysis of AI contractors", "url": "http://example.com/report"}
        ]
        comp = self.pc.compile_outline(
            ui_outline={"headline": "Test", "preview": "", "main_story": {"heading": "Main", "key_points": [], "target_word_count": 100}},
            style_metrics={},
            source_pool=srcs,
            kb_pool=[]
        )
        self.assertEqual(len(comp.source_pool_refs), 1)

    def test_platform_boilerplate_filtered(self):
        stype = self.pc.classify_source("Follow us on TikTok", {"title": "Follow us"})
        self.assertEqual(stype, SourceType.PLATFORM_BOILERPLATE)

    def test_prompt_no_marketing_language(self):
        comp = self.pc.compile_outline(
            ui_outline={"headline": "Test", "preview": "", "main_story": {"heading": "Main", "key_points": [], "target_word_count": 100}},
            style_metrics={},
            source_pool=[{"title": "Join WhatsApp", "summary": "Follow us on WhatsApp"}],
            kb_pool=[]
        )
        self.assertEqual(len(comp.source_pool_refs), 0)


if __name__ == "__main__":
    unittest.main()
