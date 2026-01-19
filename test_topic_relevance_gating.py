"""
Unit tests for topic relevance gating end-to-end.

Tests KB drift prevention, facts filtering, provided sources enforcement,
placeholder bullet rejection, and hook sanitization.
"""

import unittest
from newsletter_engine import (
    PromptConstructor, NewsletterPlan, StyleProfile, NewsletterSection,
    AnchoredOutline, AnchoredSection, AnchoredBullet, RetrievalPack, RetrievalExcerpt
)
from topic_signature import build_topic_signature, TopicSignature
from relevance_filter import score_source_relevance, filter_editorial_sources_by_topic
from image_service import _sanitize_visual_prompt


class TopicRelevanceGatingTests(unittest.TestCase):
    
    def setUp(self):
        self.pc = PromptConstructor()
    
    def test_kb_drift_filter(self):
        """Test 1: KB sources about unrelated topics (grants, labor) are filtered out."""
        # Topic: Grok undressing deepfakes
        plan = NewsletterPlan(
            theme="Grok's deepfake undressing tool targeting women in hijabs and saris",
            audience="Newsrooms",
            purpose="Investigate harm",
            angle_choices=["Platform accountability for non-consensual AI imagery"],
            required_inputs_coverage=[],
            style_profile=StyleProfile(),
            sections=[],
            call_to_action="",
            fact_risk_flags=[],
            outline_text="",
            target_length=800
        )
        
        # Unrelated KB sources
        kb_sources = [
            {
                'title': 'OpenAI grant funding for newsrooms criticized as grantwashing',
                'summary': 'OpenAI announced grants for journalism, but critics say it is PR',
                'text': 'The company pledged funding to news organizations.',
                'source_type': 'knowledge_base'
            },
            {
                'title': 'AI labor predictions for 2026',
                'summary': 'Analysts predict AI will displace workers in creative industries',
                'text': 'Labor market shifts expected as AI tools become more sophisticated.',
                'source_type': 'knowledge_base'
            }
        ]
        
        # Provided sources (relevant)
        provided_sources = [
            {
                'title': "Grok's image generator is creating realistic undressing images",
                'url': 'https://www.wired.com/story/grok-deepfake-undressing/',
                'source_type': 'provided_source'
            }
        ]
        
        # Build topic signature
        topic_sig = build_topic_signature(plan, {}, provided_sources, [])
        
        # Filter KB sources
        filtered_kb = filter_editorial_sources_by_topic(
            kb_sources, topic_sig, section_id=None, min_score=2.0
        )
        
        # Assert: KB filtered out (after == 0)
        self.assertEqual(len(filtered_kb), 0, "Unrelated KB sources should be filtered out")
    
    def test_relevant_kb_retained(self):
        """Test 2: KB source about Grok/deepfakes is retained."""
        plan = NewsletterPlan(
            theme="Grok's deepfake undressing tool targeting women in hijabs and saris",
            audience="Newsrooms",
            purpose="Investigate harm",
            angle_choices=["Platform accountability"],
            required_inputs_coverage=[],
            style_profile=StyleProfile(),
            sections=[],
            call_to_action="",
            fact_risk_flags=[],
            outline_text="",
            target_length=800
        )
        
        kb_sources = [
            {
                'title': 'Non-consensual deepfake undressing tools target women in hijabs',
                'summary': 'Grok has enabled creation of synthetic undressing images',
                'text': 'Women wearing hijabs and saris have been targeted by non-consensual deepfake imagery.',
                'source_type': 'knowledge_base'
            }
        ]
        
        topic_sig = build_topic_signature(plan, {}, [], [])
        filtered_kb = filter_editorial_sources_by_topic(kb_sources, topic_sig, min_score=2.0)
        
        # Assert: relevant KB retained
        self.assertEqual(len(filtered_kb), 1, "Relevant KB source should be retained")
    
    def test_facts_filter(self):
        """Test 3: Irrelevant facts are filtered, optional context capped."""
        plan = NewsletterPlan(
            theme="Grok deepfakes",
            audience="Newsrooms",
            purpose="Investigate",
            angle_choices=["Harm"],
            required_inputs_coverage=[],
            style_profile=StyleProfile(),
            sections=[],
            call_to_action="",
            fact_risk_flags=[],
            outline_text="",
            target_length=800
        )
        
        facts = [
            {'text': 'OpenAI granted $5M to journalism programs', 'is_optional_context': False},
            {'text': 'AI labor market expected to shift in 2026', 'is_optional_context': True},
            {'text': 'Grok generated 10,000 deepfake images in first week', 'is_optional_context': False},
        ]
        
        topic_sig = build_topic_signature(plan, {}, [], [])
        filtered_facts, metrics = self.pc.filter_facts_by_topic(facts, topic_sig, [])
        
        # Assert: only relevant fact + at most 1 optional context
        relevant_count = len([f for f in filtered_facts if not f.get('is_optional_context')])
        optional_count = len([f for f in filtered_facts if f.get('is_optional_context')])
        
        self.assertGreaterEqual(relevant_count, 1, "At least one relevant fact should be retained")
        self.assertLessEqual(optional_count, 1, "Optional context capped to 1")
        self.assertIn('Grok', filtered_facts[0]['text'], "Relevant fact about Grok should be first")
    
    def test_must_use_provided_sources(self):
        """Test 4: Plan validation fails if provided sources not anchored."""
        plan = NewsletterPlan(
            theme="Grok deepfakes",
            audience="Newsrooms",
            purpose="Investigate",
            angle_choices=["Harm"],
            required_inputs_coverage=[],
            style_profile=StyleProfile(),
            sections=[NewsletterSection(id="main", name="Main", goal="Explain", word_count=500)],
            call_to_action="",
            fact_risk_flags=[],
            outline_text="",
            target_length=800,
            must_use_provided_sources_min=1
        )
        
        # Outline WITHOUT provided source anchors
        anchored_outline = AnchoredOutline(
            sections=[
                AnchoredSection(
                    section_id="main",
                    bullets=[
                        AnchoredBullet(
                            text="Deepfakes are a problem",
                            anchors=["KB_1", "F_1"],  # No PS_ anchors
                            intent="argument"
                        )
                    ]
                )
            ]
        )
        
        # Validate
        errors = self.pc._validate_provided_sources_usage(plan, anchored_outline)
        
        # Assert: validation fails
        self.assertGreater(len(errors), 0, "Validation should fail without provided source anchors")
        self.assertIn("provided source", errors[0].lower())
    
    def test_placeholder_bullets_rejected(self):
        """Test 5: Outline with placeholder bullets is rejected."""
        topic_sig = TopicSignature(
            theme="Grok deepfakes",
            angles=["Harm"],
            entities={"Grok", "X"},
            keywords={"deepfake", "undressing", "consent"},
            exclude_keywords=set()
        )
        
        # Outline with placeholder
        anchored_outline = AnchoredOutline(
            sections=[
                AnchoredSection(
                    section_id="main",
                    bullets=[
                        AnchoredBullet(
                            text="Key point 1: supporting the goal",
                            anchors=["PS_1"],
                            intent="argument"
                        )
                    ]
                )
            ]
        )
        
        # Validate
        errors = self.pc._validate_outline_semantics(anchored_outline, topic_sig)
        
        # Assert: validation fails
        self.assertGreater(len(errors), 0, "Placeholder bullets should be rejected")
        self.assertIn("placeholder", errors[0].lower())
    
    def test_semantic_bullets_pass(self):
        """Test: Semantic bullets with topic keywords pass validation."""
        topic_sig = TopicSignature(
            theme="Grok deepfakes",
            angles=["Platform accountability"],
            entities={"Grok", "X"},
            keywords={"deepfake", "undressing", "consent", "verification"},
            exclude_keywords=set()
        )
        
        # Outline with semantic bullets
        anchored_outline = AnchoredOutline(
            sections=[
                AnchoredSection(
                    section_id="main",
                    bullets=[
                        AnchoredBullet(
                            text="Grok's lack of verification enables non-consensual deepfake creation",
                            anchors=["PS_1", "KB_1"],
                            intent="argument"
                        ),
                        AnchoredBullet(
                            text="Platform policy changes needed to prevent harm",
                            anchors=["F_1"],
                            intent="argument"
                        )
                    ]
                )
            ]
        )
        
        # Validate
        errors = self.pc._validate_outline_semantics(anchored_outline, topic_sig)
        
        # Assert: no errors
        self.assertEqual(len(errors), 0, "Semantic bullets should pass validation")
    
    def test_hook_sanitization(self):
        """Test 6: Unsafe hook prompt is sanitized."""
        # Unsafe input
        unsafe_hook = "Image of women being digitally stripped by AI tool"
        
        # Sanitize
        safe_hook, was_sanitized = _sanitize_visual_prompt(unsafe_hook)
        
        # Assert: sanitized and safe
        self.assertTrue(was_sanitized, "Unsafe prompt should be sanitized")
        self.assertNotIn("strip", safe_hook.lower())
        self.assertNotIn("women", safe_hook.lower())
        # Should contain safe alternative words
        safe_terms = ["illustration", "sketch", "collage", "shield", "verification", "warning"]
        has_safe_term = any(term in safe_hook.lower() for term in safe_terms)
        self.assertTrue(has_safe_term, f"Sanitized hook should contain safe terms, got: {safe_hook}")
    
    def test_safe_hook_unchanged(self):
        """Test: Safe hook prompt is not changed."""
        safe_hook = "Abstract illustration of AI verification systems"
        
        sanitized, was_sanitized = _sanitize_visual_prompt(safe_hook)
        
        self.assertFalse(was_sanitized, "Safe prompt should not be sanitized")
        self.assertEqual(safe_hook, sanitized)
    
    def test_fact_scoring_relevance(self):
        """Test: Fact relevance scoring works correctly."""
        topic_sig = TopicSignature(
            theme="Grok deepfakes",
            angles=["Harm"],
            entities={"Grok", "X", "Elon"},
            keywords={"deepfake", "undressing", "consent", "women"},
            exclude_keywords={"grant", "funding", "labor"}
        )
        
        # Relevant fact
        relevant_text = "Grok generated 10,000 deepfake undressing images targeting women"
        score_relevant = score_source_relevance(relevant_text, topic_sig)
        
        # Irrelevant fact
        irrelevant_text = "OpenAI announced grant funding for journalism programs"
        score_irrelevant = score_source_relevance(irrelevant_text, topic_sig)
        
        # Assert: relevant scores higher
        self.assertGreater(score_relevant, 2.0, "Relevant fact should score above threshold")
        self.assertLess(score_irrelevant, 2.0, "Irrelevant fact should score below threshold")


if __name__ == '__main__':
    unittest.main()
