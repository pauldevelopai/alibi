import unittest

from newsletter_engine import PromptConstructor, NewsletterPlan, NewsletterSection, RequiredInputCoverage, StyleProfile, RetrievalPack, RetrievalExcerpt


class AuditFixTests(unittest.TestCase):
    def setUp(self):
        self.pc = PromptConstructor()

        self.plan = {
            "sections": [
                {"id": "main", "name": "Main", "word_count": 10, "goal": "", "sources_needed_min": 1, "source_anchor_requirements": ["outline"]}
            ],
            "required_inputs_coverage": [{"input_type": "outline", "must_use": True}],
            "style_profile": {"style_tokens": ["conversational"]}
        }

        self.pack = {
            "excerpts": [
                {"id": "E_1", "text": "data shows growth", "fingerprint_terms": ["growth", "data"]},
            ]
        }

    def test_missing_point_is_added(self):
        plan = dict(self.plan, must_include_points=["do this"])
        audit = self.pc.audit_coverage(plan=plan, pack=self.pack, outline="outline", draft_text="short draft")
        fixed = self.pc.apply_fixes("short draft", audit, plan, self.pack, "outline")
        self.assertIn("do this", fixed)

    def test_unanchored_claim_marked(self):
        txt = "According to the study, revenue increased 20 percent."
        audit = self.pc.audit_coverage(plan=self.plan, pack=self.pack, outline="outline", draft_text=txt)
        fixed = self.pc.apply_fixes(txt, audit, self.plan, self.pack, "outline")
        self.assertIn("needs verification", fixed)

    def test_compliant_passes(self):
        txt = "Growth is visible. conversational tone present. data shows growth."
        audit = self.pc.audit_coverage(plan=self.plan, pack=self.pack, outline="outline", draft_text=txt)
        self.assertTrue(audit.get("pass", False))


if __name__ == "__main__":
    unittest.main()
