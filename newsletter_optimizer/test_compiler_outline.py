import unittest

from newsletter_engine import PromptConstructor, CompilerKeyPoint, CompilerOutline, NewsletterPlan, StyleProfile, NewsletterSection


class CompilerOutlineTests(unittest.TestCase):
    def setUp(self):
        self.pc = PromptConstructor()

    def test_key_point_classification(self):
        ui_outline = {
            "headline": "AI grants",
            "preview": "OpenAI funding",
            "main_story": {
                "heading": "Main",
                "key_points": [
                    "According to the report, funding is $2 million.",
                    "We should look critically at motives.",
                    "This is a call to subscribe."
                ],
                "target_word_count": 200
            }
        }
        comp = self.pc.compile_outline(ui_outline, style_metrics={}, source_pool=[], kb_pool=[])
        facts = [kp for sec in comp.sections for kp in sec['key_points'] if kp['kind'] == 'FACT']
        ctas = [kp for sec in comp.sections for kp in sec['key_points'] if kp['kind'] == 'CTA']
        self.assertTrue(any(kp['needs_citation'] for kp in facts))
        self.assertTrue(len(ctas) >= 1)

    def test_ui_artifact_filtered(self):
        ui_outline = {
            "headline": "Test",
            "preview": "Prev",
            "avoid_points": [],
            "main_story": {"heading": "Main", "key_points": [], "target_word_count": 100}
        }
        comp = self.pc.compile_outline(ui_outline, style_metrics={}, source_pool=[], kb_pool=[])
        self.assertIn("Created with ChatGPT", comp.avoid_points[0])

    def test_compile_outline_pools_not_injected(self):
        ui_outline = {"headline": "Test", "preview": "Prev", "main_story": {"heading": "Main", "key_points": [], "target_word_count": 100}}
        sources = [{"title": f"Src {i}", "url": f"http://example.com/{i}"} for i in range(10)]
        comp = self.pc.compile_outline(ui_outline, style_metrics={}, source_pool=sources, kb_pool=[])
        self.assertLessEqual(len(comp.source_pool_refs), 8)


if __name__ == "__main__":
    unittest.main()
