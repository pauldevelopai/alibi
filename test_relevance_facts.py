import unittest

from newsletter_engine import PromptConstructor, NewsletterPlan, StyleProfile, CompilerOutline


class RelevanceFactsTests(unittest.TestCase):
    def test_relevance_prioritizes_facts(self):
        pc = PromptConstructor()
        comp = CompilerOutline(
            headline="AI contractors",
            preview="contractor uploads",
            opening_hook="",
            central_question="Are contractors at risk?",
            stance="critical",
            target_word_count=400,
            story_type="news_analysis",
            sections=[{
                "section_id": "main",
                "title": "Main",
                "focus": "Risk",
                "word_count": 200,
                "key_points": [
                    {"id": "kp1", "text": "Contractors uploading real work", "kind": "FACT", "priority": 1, "needs_citation": True, "suggested_sources": []}
                ]
            }],
            must_include_points=[],
            avoid_points=[],
            source_pool_refs=[],
            kb_pool_refs=[],
        )
        plan = NewsletterPlan(
            theme="AI contractors",
            audience="",
            purpose="",
            angle_choices=["contractor risk"],
            required_inputs_coverage=[],
            style_profile=StyleProfile(),
            sections=[],
            call_to_action="",
            fact_risk_flags=[],
            outline_text="",
            target_length=400,
            compiler_outline=comp,
        )
        facts = [{"id": "f1", "text": "Contractors uploading real work", "source_title": "TechCrunch"}]
        rag = [{"text": "Other unrelated story", "newsletter_title": "Other"}]
        brief = pc.build_relevance_brief(plan, facts, rag, [], compiler_outline=comp)
        kb = [r for r in brief.selected_items if r.source_type == "knowledge_base"]
        self.assertTrue(any("Contractors" in r.summary or "Contractors" in r.title for r in kb))


if __name__ == "__main__":
    unittest.main()
