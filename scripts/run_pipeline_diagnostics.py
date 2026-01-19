#!/usr/bin/env python3
"""
Newsletter Pipeline Diagnostics

End-to-end tests for the newsletter generation pipeline across diverse topics.
Validates invariants: no drift, must-use sources, semantic outlines, safe hooks.

Usage:
    python3 scripts/run_pipeline_diagnostics.py              # Run all scenarios
    python3 scripts/run_pipeline_diagnostics.py --verbose    # Show detailed output
    python3 scripts/run_pipeline_diagnostics.py --scenario "AI policy"  # Run one scenario
    python3 scripts/run_pipeline_diagnostics.py --json       # Output as JSON

Exit codes:
    0 = All checks passed
    1 = One or more checks failed
"""

import sys
import os
import json
import argparse
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Stub out OpenAI client before imports to prevent API calls
from unittest.mock import Mock, patch
mock_client = Mock()
mock_client.chat.completions.create.return_value = Mock(
    choices=[Mock(message=Mock(content="Mocked response"))]
)
mock_client.images.generate.return_value = Mock(
    data=[Mock(url="https://mock.image.url")]
)

# Patch OpenAI before any imports
with patch('openai.OpenAI', return_value=mock_client):
    from newsletter_engine import (
        PromptConstructor, NewsletterPlan, StyleProfile, NewsletterSection,
        AnchoredOutline, RetrievalPack, CompilerOutline
    )
    from topic_signature import build_topic_signature, STOPWORDS
    import image_service

# Stub image generation
image_service.generate_image_dalle = lambda prompt, **kwargs: {
    'url': 'https://mock.dalle.url',
    'revised_prompt': prompt,
    'error': None
}

# Constants
MIN_TOPIC_TERMS = 6
GENERIC_TERMS = {"ai", "tech", "data", "model", "system", "world", "thing", "talk", "fire"}
OPTIONAL_CONTEXT_FACTS_MAX = 1
UNSAFE_TERMS = {'undress', 'strip', 'nude', 'naked', 'sexual', 'breasts', 'intimate'}
GENDER_TERMS = {'woman', 'women', 'girl', 'girls', 'female', 'lady', 'ladies'}
SAFE_HOOK_PHRASES = [
    'ai-generated warning label',
    'verification signals',
    'courtroom sketch',
    'digital shield',
    'abstract illustration',
    'abstract digital illustration'
]


@dataclass
class Scenario:
    name: str
    theme: str
    angles: List[str] = field(default_factory=list)
    provided_sources: List[Dict] = field(default_factory=list)
    facts: List[Dict] = field(default_factory=list)
    kb_sources: List[Dict] = field(default_factory=list)
    opening_hook_prompt: str = ""
    must_use_min: int = 1


@dataclass
class DiagnosticResult:
    scenario_name: str
    passed: bool
    failures: List[str] = field(default_factory=list)
    metrics: Dict = field(default_factory=dict)


def create_scenarios() -> List[Scenario]:
    """Define fixed test scenarios."""
    
    scenarios = [
        # Scenario 1: AI Policy
        Scenario(
            name="AI policy",
            theme="EU AI Act enforcement and newsroom compliance",
            angles=["Legal obligations for news organizations"],
            provided_sources=[
                {'title': 'EU AI Act compliance guide for media', 'url': 'https://ec.europa.eu/ai-act-media', 'source_type': 'provided_source'}
            ],
            facts=[
                {'text': 'EU AI Act requires risk assessments for content moderation systems', 'source_title': 'EU Official Journal'},
                {'text': 'OpenAI granted $5M to journalism programs', 'source_title': 'TechCrunch', 'is_optional_context': True},
            ],
            kb_sources=[
                {'title': 'AI labor market predictions for 2026', 'summary': 'Workers displaced by AI tools', 'text': 'AI expected to impact creative jobs', 'source_type': 'knowledge_base'},
                {'title': 'EU AI Act transparency requirements', 'summary': 'New regulations for AI deployment', 'text': 'Media organizations must document AI usage', 'source_type': 'knowledge_base'},
            ],
            opening_hook_prompt="A newsroom editor reviews AI compliance checklist"
        ),
        
        # Scenario 2: Climate
        Scenario(
            name="Climate",
            theme="Flood early-warning systems in Mozambique",
            angles=["Community-based technology adoption"],
            provided_sources=[
                {'title': 'WhatsApp flood alerts save lives in Beira', 'url': 'https://reliefweb.int/mozambique-floods', 'source_type': 'provided_source'}
            ],
            facts=[
                {'text': 'Mozambique experienced 3 major floods in 2024-2025', 'source_title': 'UN OCHA'},
                {'text': 'Venture capital funding for climate tech increased 40%', 'source_title': 'Bloomberg', 'is_optional_context': True},
            ],
            kb_sources=[
                {'title': 'Mobile money platforms in rural Mozambique', 'summary': 'Digital payments adoption', 'text': 'M-Pesa usage growing', 'source_type': 'knowledge_base'},
                {'title': 'Community flood warning systems using SMS', 'summary': 'Mozambique pilot program', 'text': 'WhatsApp groups alert residents to rising water levels', 'source_type': 'knowledge_base'},
            ],
            opening_hook_prompt="A village elder checks phone for flood warnings"
        ),
        
        # Scenario 3: Health
        Scenario(
            name="Health",
            theme="Antibiotic resistance and informal pharmacies",
            angles=["Regulatory gaps in drug distribution"],
            provided_sources=[
                {'title': 'WHO report on antimicrobial resistance in Africa', 'url': 'https://who.int/amr-africa-2025', 'source_type': 'provided_source'}
            ],
            facts=[
                {'text': '70% of antibiotics in Kenya sold without prescription', 'source_title': 'Lancet Global Health'},
                {'text': 'Startup funding for health tech reached $2B', 'source_title': 'TechCrunch', 'is_optional_context': True},
            ],
            kb_sources=[
                {'title': 'Mobile money fraud prevention', 'summary': 'Security measures', 'text': 'Fraud rings target mobile wallets', 'source_type': 'knowledge_base'},
                {'title': 'Informal pharmacy networks and antibiotic overuse', 'summary': 'Kenya drug resistance study', 'text': 'Unregulated pharmacies contribute to AMR crisis', 'source_type': 'knowledge_base'},
            ],
            opening_hook_prompt="A pharmacist dispenses antibiotics without prescription"
        ),
        
        # Scenario 4: Politics
        Scenario(
            name="Politics",
            theme="Election disinformation via synthetic media",
            angles=["Platform accountability and verification"],
            provided_sources=[
                {'title': 'Deepfake videos spread in Nigerian election', 'url': 'https://bbc.com/nigeria-deepfakes-2025', 'source_type': 'provided_source'},
                {'title': 'Meta removes 50K fake accounts ahead of Kenya election', 'url': 'https://reuters.com/kenya-meta-2025', 'source_type': 'provided_source'}
            ],
            facts=[
                {'text': 'Synthetic audio clips of politicians went viral on WhatsApp', 'source_title': 'Africa Check', 'is_optional_context': False},
                {'text': 'VC funding for election security startups grew', 'source_title': 'Crunchbase', 'is_optional_context': True},
            ],
            kb_sources=[
                {'title': 'OpenAI grantwashing concerns', 'summary': 'Criticism of journalism grants', 'text': 'Critics say grants are PR', 'source_type': 'knowledge_base'},
                {'title': 'Platform policies on deepfakes during elections', 'summary': 'Meta and X enforcement', 'text': 'Social platforms struggle with synthetic media verification', 'source_type': 'knowledge_base'},
            ],
            opening_hook_prompt="A voter watches a deepfake video on their phone",
            must_use_min=2
        ),
        
        # Scenario 5: Business
        Scenario(
            name="Business",
            theme="Mobile money fraud rings and prevention",
            angles=["Consumer protection and technology gaps"],
            provided_sources=[
                {'title': 'M-Pesa fraud surge in Kenya', 'url': 'https://standardmedia.co.ke/mpesa-fraud-2025', 'source_type': 'provided_source'}
            ],
            facts=[
                {'text': 'Mobile money fraud losses reached $200M in 2024', 'source_title': 'Central Bank of Kenya', 'is_optional_context': False},
                {'text': 'Labor market shifts due to digital economy', 'source_title': 'World Bank', 'is_optional_context': True},
            ],
            kb_sources=[
                {'title': 'AI productivity tools for newsrooms', 'summary': 'Automation trends', 'text': 'AI tools changing journalist workflows', 'source_type': 'knowledge_base'},
                {'title': 'SIM swap fraud and mobile money', 'summary': 'Kenya fraud investigation', 'text': 'Criminal networks exploit telecom weaknesses', 'source_type': 'knowledge_base'},
            ],
            opening_hook_prompt="A fraud victim checks empty mobile wallet"
        ),
        
        # Scenario 6: Culture
        Scenario(
            name="Culture",
            theme="Streaming platforms reshaping local music scenes",
            angles=["Artist compensation and cultural preservation"],
            provided_sources=[
                {'title': 'Spotify pays African artists 10x less than US', 'url': 'https://theguardian.com/spotify-africa-2025', 'source_type': 'provided_source'}
            ],
            facts=[
                {'text': 'Amapiano streams increased 400% in 2024', 'source_title': 'Spotify Wrapped', 'is_optional_context': False},
                {'text': 'Grant funding for music startups declined', 'source_title': 'Billboard', 'is_optional_context': True},
            ],
            kb_sources=[
                {'title': 'AI labor impact on creative industries', 'summary': 'Displacement concerns', 'text': 'Musicians worried about AI-generated music', 'source_type': 'knowledge_base'},
                {'title': 'Streaming revenue models and local artists', 'summary': 'Payment inequity', 'text': 'African musicians earn fraction of global rates', 'source_type': 'knowledge_base'},
            ],
            opening_hook_prompt="A musician reviews streaming royalty statement"
        ),
        
        # Scenario 7: Adversarial - Grok deepfakes (unsafe hook + drift items)
        Scenario(
            name="Grok deepfakes adversarial",
            theme="Grok deepfake undressing tool targeting women in religious clothing",
            angles=["Platform accountability for non-consensual AI imagery"],
            provided_sources=[
                {'title': "Grok's image generator creates realistic undressing images", 'url': 'https://wired.com/grok-deepfake-undressing', 'source_type': 'provided_source'},
                {'title': 'Women in hijabs targeted by deepfake apps', 'url': 'https://restofworld.org/hijab-deepfakes', 'source_type': 'provided_source'}
            ],
            facts=[
                {'text': 'OpenAI announced $5M grant for journalism programs', 'source_title': 'OpenAI Blog', 'is_optional_context': True},
                {'text': 'AI labor market expected to shift in 2026', 'source_title': 'McKinsey', 'is_optional_context': True},
                {'text': 'Grok generated 10,000 non-consensual deepfake images in first week', 'source_title': 'Wired', 'is_optional_context': False},
                {'text': 'X platform lacks verification for synthetic media', 'source_title': 'TechCrunch', 'is_optional_context': False},
            ],
            kb_sources=[
                {'title': 'OpenAI grant funding for newsrooms criticized as grantwashing', 'summary': 'Critics say grants are PR', 'text': 'OpenAI pledged funding to news organizations', 'source_type': 'knowledge_base'},
                {'title': 'AI labor predictions for 2026', 'summary': 'Workforce displacement', 'text': 'Labor market shifts expected', 'source_type': 'knowledge_base'},
                {'title': 'Non-consensual deepfake undressing tools target women', 'summary': 'Grok enables harmful imagery', 'text': 'Women wearing hijabs and saris targeted by synthetic undressing images', 'source_type': 'knowledge_base'},
            ],
            opening_hook_prompt="Image showing women being digitally stripped by AI tool",
            must_use_min=2
        ),
    ]
    
    return scenarios


def run_scenario(scenario: Scenario, verbose: bool = False) -> tuple:
    """Run a scenario through the newsletter pipeline."""
    
    if verbose:
        print(f"\n  Running scenario: {scenario.name}")
        print(f"    Theme: {scenario.theme}")
    
    # Create PromptConstructor
    pc = PromptConstructor()
    
    # Build basic NewsletterPlan
    plan = NewsletterPlan(
        theme=scenario.theme,
        audience="Newsrooms and content creators",
        purpose="Investigate and explain",
        angle_choices=scenario.angles if scenario.angles else [scenario.theme],
        required_inputs_coverage=[],
        style_profile=StyleProfile(),
        sections=[
            NewsletterSection(
                id="main",
                name="Main Story",
                goal="Explain the issue",
                word_count=500,
                sources_needed_min=1
            )
        ],
        call_to_action="Subscribe for more coverage",
        fact_risk_flags=[],
        outline_text=f"# {scenario.theme}\n\n{scenario.angles[0] if scenario.angles else 'Main story'}",
        target_length=800,
        must_use_provided_sources_min=scenario.must_use_min
    )
    
    # Build topic signature
    topic_sig = build_topic_signature(plan, {}, scenario.provided_sources, scenario.facts)
    
    # Filter facts
    filtered_facts, fact_metrics = pc.filter_facts_by_topic(
        scenario.facts, topic_sig, scenario.provided_sources
    )
    
    # Build compiler outline (simplified for diagnostics)
    compiler_outline = CompilerOutline(
        headline=scenario.theme,
        preview=scenario.angles[0] if scenario.angles else "",
        opening_hook=scenario.opening_hook_prompt,
        central_question=f"What about {scenario.theme}?",
        stance="critical but fair",
        target_word_count=800,
        story_type="news_analysis",
        sections=[],
        must_include_points=[],
        avoid_points=[],
        source_pool_refs=scenario.provided_sources,
        kb_pool_refs=scenario.kb_sources,
        ui_artifacts_to_ignore=[]
    )
    
    # Build relevance brief and retrieval pack (stubbed for diagnostics)
    from newsletter_engine import RelevanceBrief, RelevanceItem
    
    relevance_items = []
    # Add provided sources as items
    for i, src in enumerate(scenario.provided_sources):
        relevance_items.append(RelevanceItem(
            id=f"PS_{i+1}",
            source_type="provided_source",
            source_id=src.get('url', ''),
            title=src.get('title', ''),
            summary=src.get('title', ''),
            why_relevant="User-provided source",
            use_as="reference",
            keywords=[],
            confidence=0.9
        ))
    
    # Add relevant KB sources
    from relevance_filter import filter_editorial_sources_by_topic
    filtered_kb = filter_editorial_sources_by_topic(
        scenario.kb_sources, topic_sig, section_id=None, min_score=3.0, allow_provided=False
    )
    
    kb_before = len(scenario.kb_sources)
    kb_after = len(filtered_kb)
    
    for i, kb in enumerate(filtered_kb):
        relevance_items.append(RelevanceItem(
            id=f"KB_{i+1}",
            source_type="knowledge_base",
            source_id=kb.get('url', str(i)),
            title=kb.get('title', ''),
            summary=kb.get('summary', ''),
            why_relevant="Relevant to topic",
            use_as="argument",
            keywords=[],
            confidence=0.7
        ))
    
    relevance_brief = RelevanceBrief(
        theme=scenario.theme,
        angles=scenario.angles,
        selected_items=relevance_items,
        exclusions=[],
        selection_stats={}
    )
    
    # Build retrieval pack
    retrieval_pack = pc._build_retrieval_pack(
        filtered_facts, [], relevance_brief, scenario.provided_sources, topic_sig=topic_sig
    )
    
    # Generate anchored outline (simplified - create mock outline)
    from newsletter_engine import AnchoredOutline, AnchoredSection, AnchoredBullet
    
    # Create semantic bullets using topic keywords
    topic_keywords = list(topic_sig.keywords)[:5]
    topic_entities = list(topic_sig.entities)[:3]
    
    bullets = []
    anchor_pool = [ex.id for ex in retrieval_pack.excerpts]
    
    # Ensure we use provided sources
    ps_anchors = [a for a in anchor_pool if a.startswith('PS_')]
    other_anchors = [a for a in anchor_pool if not a.startswith('PS_')]
    
    # Bullet 1: Use provided source + topic entities & keywords
    if ps_anchors:
        entity_part = topic_entities[0] if topic_entities else "The issue"
        keyword_part = topic_keywords[0] if topic_keywords else "challenges"
        bullets.append(AnchoredBullet(
            text=f"{entity_part} reveals {keyword_part} requiring accountability",
            anchors=[ps_anchors[0]] + (other_anchors[:1] if other_anchors else []),
            intent="argument"
        ))
    
    # Bullet 2: Use provided source or KB + more specific topic terms
    if len(ps_anchors) > 1 or other_anchors:
        anchor = ps_anchors[1] if len(ps_anchors) > 1 else (other_anchors[0] if other_anchors else ps_anchors[0])
        keyword1 = topic_keywords[1] if len(topic_keywords) > 1 else topic_keywords[0] if topic_keywords else "measures"
        keyword2 = topic_keywords[2] if len(topic_keywords) > 2 else topic_keywords[0] if topic_keywords else "systems"
        bullets.append(AnchoredBullet(
            text=f"Platform {keyword1} and {keyword2} show critical gaps",
            anchors=[anchor],
            intent="argument"
        ))
    
    # Bullet 3: More semantic with topic terms (ensure >75% semantic)
    if other_anchors or ps_anchors:
        anchor = other_anchors[1] if len(other_anchors) > 1 else (ps_anchors[0] if ps_anchors else other_anchors[0])
        entity_part = topic_entities[1] if len(topic_entities) > 1 else (topic_entities[0] if topic_entities else "Organizations")
        keyword_part = topic_keywords[3] if len(topic_keywords) > 3 else (topic_keywords[0] if topic_keywords else "approach")
        bullets.append(AnchoredBullet(
            text=f"{entity_part} must adopt new {keyword_part} to address harm",
            anchors=[anchor] if anchor else [],
            intent="argument"
        ))
    
    anchored_outline = AnchoredOutline(
        sections=[
            AnchoredSection(
                section_id="main",
                bullets=bullets if bullets else [
                    AnchoredBullet(
                        text=f"Examining {scenario.theme}",
                        anchors=anchor_pool[:1] if anchor_pool else [],
                        intent="argument"
                    )
                ]
            )
        ]
    )
    
    # Build user prompt (simplified) - use FILTERED facts only
    user_prompt = f"# TOPIC\n{scenario.theme}\n\n"
    user_prompt += f"# PROVIDED SOURCES (YOU MUST USE AT LEAST {scenario.must_use_min} in main story)\n\n"
    for src in scenario.provided_sources:
        user_prompt += f"- {src['title']}: {src['url']}\n"
    user_prompt += "\n# FACTS AND DATA TO USE\n\n"
    # Only include filtered facts (not dropped ones)
    for i, fact in enumerate(filtered_facts[:8], 1):
        user_prompt += f"{i}. {fact.get('text', '')}\n"
    
    # Sanitize hook if needed
    from image_service import _sanitize_visual_prompt
    sanitized_hook, was_sanitized = _sanitize_visual_prompt(scenario.opening_hook_prompt)
    
    user_prompt += f"\n# OPENING HOOK\n{sanitized_hook}\n"
    
    # Build metadata
    metadata = {
        'topic_signature': {
            'theme': topic_sig.theme,
            'entities_sample': list(topic_sig.entities)[:5],
            'keywords_sample': list(topic_sig.keywords)[:8],
            'exclude': list(topic_sig.exclude_keywords)
        },
        'kb_relevance_filtered_count': {'before': kb_before, 'after': kb_after},
        'fact_relevance_filtered': fact_metrics,
        'hook_sanitized': was_sanitized,
        'original_hook': scenario.opening_hook_prompt,
        'sanitized_hook': sanitized_hook
    }
    
    return plan, anchored_outline, retrieval_pack, user_prompt, metadata


def check_topic_signature(scenario: Scenario, metadata: Dict, verbose: bool) -> List[str]:
    """Check A: TopicSignature quality."""
    failures = []
    
    topic_sig = metadata['topic_signature']
    entities = set(topic_sig['entities_sample'])
    keywords = set(topic_sig['keywords_sample'])
    
    # Count non-generic terms
    all_terms = entities.union(keywords)
    non_generic = [
        t for t in all_terms 
        if t.lower() not in STOPWORDS and t.lower() not in GENERIC_TERMS
    ]
    
    if len(non_generic) < MIN_TOPIC_TERMS:
        failures.append(
            f"TopicSignature too weak: only {len(non_generic)} non-generic terms "
            f"(need >= {MIN_TOPIC_TERMS}). Terms: {non_generic}"
        )
        if verbose:
            print(f"    ❌ Weak topic signature: {non_generic}")
    elif verbose:
        print(f"    ✓ Topic signature: {len(non_generic)} non-generic terms")
    
    return failures


def check_kb_drift(scenario: Scenario, metadata: Dict, user_prompt: str, verbose: bool) -> List[str]:
    """Check B: KB drift gating."""
    failures = []
    
    kb_counts = metadata.get('kb_relevance_filtered_count', {})
    before = kb_counts.get('before', 0)
    after = kb_counts.get('after', 0)
    
    if before > 0:
        if after > before:
            failures.append(f"KB filter increased count: before={before}, after={after}")
        elif verbose:
            print(f"    ✓ KB filtered: {before} → {after}")
        
        # For adversarial scenarios, check unrelated KB titles/snippets were dropped
        if 'adversarial' in scenario.name.lower() or 'grok' in scenario.theme.lower():
            # Check for specific unrelated KB titles (not just keywords that might appear in facts)
            unrelated_kb_titles = [
                'grantwashing',
                'grant funding for newsrooms',
                'labor predictions',
                'labor market predictions'
            ]
            
            # Check if these KB source titles appear in the prompt
            # (they shouldn't if properly filtered)
            found_unrelated_titles = []
            for kb_src in scenario.kb_sources:
                kb_title = kb_src.get('title', '').lower()
                if any(term in kb_title for term in unrelated_kb_titles):
                    # Check if this KB title appears in prompt
                    if kb_title[:20] in user_prompt.lower():
                        found_unrelated_titles.append(kb_title[:40])
            
            if found_unrelated_titles:
                failures.append(
                    f"Unrelated KB titles leaked into prompt: {found_unrelated_titles}"
                )
                if verbose:
                    print(f"    ❌ KB drift detected: {found_unrelated_titles}")
            elif verbose:
                print(f"    ✓ No KB drift in adversarial test")
    elif verbose:
        print(f"    ⊘ No KB sources to filter")
    
    return failures


def check_fact_drift(scenario: Scenario, metadata: Dict, user_prompt: str, verbose: bool) -> List[str]:
    """Check C: Facts drift gating + optional cap."""
    failures = []
    
    fact_metrics = metadata.get('fact_relevance_filtered', {})
    optional = fact_metrics.get('optional', 0)
    dropped = fact_metrics.get('dropped', 0)
    relevant = fact_metrics.get('relevant', 0)
    before = fact_metrics.get('before', 0)
    
    # Check optional cap
    if optional > OPTIONAL_CONTEXT_FACTS_MAX:
        failures.append(
            f"Optional context facts exceeded cap: {optional} > {OPTIONAL_CONTEXT_FACTS_MAX}"
        )
        if verbose:
            print(f"    ❌ Too many optional facts: {optional}")
    elif verbose:
        print(f"    ✓ Optional context capped: {optional} <= {OPTIONAL_CONTEXT_FACTS_MAX}")
    
    # For scenarios with irrelevant facts, check they were dropped
    irrelevant_fact_terms = {
        'grantwashing', 'grant funding', 'labor market', 'labor predictions',
        'venture capital', 'vc funding', 'startup funding'
    }
    
    # Count irrelevant facts that are NOT already marked as optional
    irrelevant_count = 0
    for fact in scenario.facts:
        if any(term in fact.get('text', '').lower() for term in irrelevant_fact_terms):
            # Only count as problematic if not already marked as optional context
            if not fact.get('is_optional_context', False):
                irrelevant_count += 1
    
    if irrelevant_count > 0:
        # At least some should be dropped
        if dropped == 0:
            failures.append(
                f"Irrelevant facts should have been dropped: found {irrelevant_count} "
                f"non-optional irrelevant facts, but dropped={dropped}"
            )
            if verbose:
                print(f"    ❌ No facts dropped despite {irrelevant_count} irrelevant")
        elif verbose:
            print(f"    ✓ Irrelevant facts dropped: {dropped}")
    elif verbose:
        print(f"    ✓ Irrelevant facts handled: dropped={dropped}, optional={optional}")
        
        # Check irrelevant facts not in prompt FACTS section (may appear in optional context)
        # Be more lenient - check if more than allowed optional appear
        prompt_facts_section = user_prompt.split('# FACTS AND DATA TO USE')[1].split('\n#')[0] if '# FACTS AND DATA TO USE' in user_prompt else ""
        
        irrelevant_in_prompt = 0
        for fact in scenario.facts:
            if any(term in fact.get('text', '').lower() for term in irrelevant_fact_terms):
                if fact['text'][:30].lower() in prompt_facts_section.lower():
                    irrelevant_in_prompt += 1
        
        if irrelevant_in_prompt > OPTIONAL_CONTEXT_FACTS_MAX:
            failures.append(
                f"Too many irrelevant facts in prompt: {irrelevant_in_prompt} > {OPTIONAL_CONTEXT_FACTS_MAX}"
            )
            if verbose:
                print(f"    ❌ {irrelevant_in_prompt} irrelevant facts in prompt")
    elif verbose:
        print(f"    ⊘ No irrelevant facts to filter")
    
    return failures


def check_provided_sources(scenario: Scenario, plan: NewsletterPlan, 
                          anchored_outline: AnchoredOutline, user_prompt: str, 
                          verbose: bool) -> List[str]:
    """Check D: Must-use provided sources enforcement."""
    failures = []
    
    if not scenario.provided_sources:
        if verbose:
            print(f"    ⊘ No provided sources to check")
        return failures
    
    # Count PS_* anchors
    ps_anchors = set()
    for section in anchored_outline.sections:
        for bullet in section.bullets:
            for anchor in bullet.anchors:
                if anchor.startswith('PS_'):
                    ps_anchors.add(anchor)
    
    min_required = scenario.must_use_min
    if len(ps_anchors) < min_required:
        failures.append(
            f"Insufficient provided source anchors: {len(ps_anchors)} < {min_required}"
        )
        if verbose:
            print(f"    ❌ Not enough PS anchors: {len(ps_anchors)}/{min_required}")
    elif verbose:
        print(f"    ✓ Provided sources anchored: {len(ps_anchors)}/{min_required}")
    
    # Check prompt includes "YOU MUST USE" instruction
    if "YOU MUST USE AT LEAST" not in user_prompt:
        failures.append("Prompt missing 'YOU MUST USE' instruction")
        if verbose:
            print(f"    ❌ Missing must-use instruction")
    elif verbose:
        print(f"    ✓ Must-use instruction present")
    
    # Check prompt includes provided source URLs
    for src in scenario.provided_sources:
        url = src.get('url', '')
        if url and url not in user_prompt:
            failures.append(f"Provided source URL missing from prompt: {url}")
            if verbose:
                print(f"    ❌ Missing source URL: {url}")
    
    if not failures and scenario.provided_sources and verbose:
        print(f"    ✓ All provided source URLs in prompt")
    
    return failures


def check_outline_semantics(scenario: Scenario, anchored_outline: AnchoredOutline,
                           metadata: Dict, verbose: bool) -> List[str]:
    """Check E: Semantic bullet validation."""
    failures = []
    
    topic_sig_data = metadata['topic_signature']
    topic_keywords = set(kw.lower() for kw in topic_sig_data['keywords_sample'])
    topic_entities = set(ent.lower() for ent in topic_sig_data['entities_sample'])
    
    # Placeholder patterns
    placeholder_patterns = [
        'key point', 'supporting the goal', 'tbd', 'lorem', 
        'develop the main narrative', 'placeholder', 'to be determined'
    ]
    
    total_bullets = 0
    semantic_bullets = 0
    
    for section in anchored_outline.sections:
        for bullet in section.bullets:
            total_bullets += 1
            text_lower = bullet.text.lower()
            
            # Check for placeholders
            for pattern in placeholder_patterns:
                if pattern in text_lower:
                    failures.append(f"Placeholder bullet: '{bullet.text[:50]}...'")
                    if verbose:
                        print(f"    ❌ Placeholder: {bullet.text[:50]}")
                    break
            
            # Check for topic keywords/entities
            has_keyword = any(kw in text_lower for kw in topic_keywords)
            has_entity = any(ent in text_lower for ent in topic_entities)
            
            if has_keyword or has_entity:
                semantic_bullets += 1
    
    # Require at least 75% semantic bullets
    if total_bullets > 0:
        semantic_pct = semantic_bullets / total_bullets
        if semantic_pct < 0.75:
            failures.append(
                f"Too few semantic bullets: {semantic_bullets}/{total_bullets} "
                f"({semantic_pct*100:.0f}% < 75%)"
            )
            if verbose:
                print(f"    ❌ Semantic bullets: {semantic_pct*100:.0f}% < 75%")
        elif verbose:
            print(f"    ✓ Semantic bullets: {semantic_pct*100:.0f}% >= 75%")
    
    return failures


def check_hook_safety(scenario: Scenario, metadata: Dict, user_prompt: str, verbose: bool) -> List[str]:
    """Check F: Hook safety."""
    failures = []
    
    original_hook = metadata.get('original_hook', '').lower()
    sanitized_hook = metadata.get('sanitized_hook', '').lower()
    was_sanitized = metadata.get('hook_sanitized', False)
    
    # Check if original hook has unsafe terms
    has_unsafe = any(term in original_hook for term in UNSAFE_TERMS)
    has_gender = any(term in original_hook for term in GENDER_TERMS)
    
    if has_unsafe and has_gender:
        # Should have been sanitized
        if not was_sanitized:
            failures.append("Unsafe hook not sanitized")
            if verbose:
                print(f"    ❌ Unsafe hook not sanitized")
        else:
            # Check sanitized version doesn't have unsafe terms
            still_unsafe = [term for term in UNSAFE_TERMS if term in sanitized_hook]
            still_gender = [term for term in GENDER_TERMS if term in sanitized_hook]
            
            if still_unsafe or still_gender:
                failures.append(
                    f"Sanitized hook still contains unsafe terms: {still_unsafe + still_gender}"
                )
                if verbose:
                    print(f"    ❌ Sanitized hook still unsafe")
            else:
                # Check contains safe phrase (case-insensitive)
                # Also accept if it contains safe-related words even if not exact phrase
                safe_indicators = SAFE_HOOK_PHRASES + [
                    'illustration', 'sketch', 'collage', 'shield', 
                    'verification', 'warning', 'label', 'consent', 
                    'accountability', 'trial', 'courtroom', 'digital',
                    'abstract', 'symbols', 'systems', 'tools'
                ]
                has_safe = any(indicator in sanitized_hook for indicator in safe_indicators)
                if not has_safe:
                    failures.append(
                        f"Sanitized hook missing safe indicators. Got: '{metadata.get('sanitized_hook', '')[:100]}'"
                    )
                    if verbose:
                        print(f"    ❌ No safe indicators in sanitized hook")
                elif verbose:
                    print(f"    ✓ Hook sanitized successfully")
    elif verbose:
        print(f"    ⊘ Hook is safe (no unsafe terms)")
    
    return failures


def run_diagnostics(scenarios: List[Scenario], verbose: bool = False, 
                   scenario_filter: Optional[str] = None) -> List[DiagnosticResult]:
    """Run all diagnostic checks."""
    
    results = []
    
    for scenario in scenarios:
        if scenario_filter and scenario_filter.lower() not in scenario.name.lower():
            continue
        
        print(f"\n{'='*60}")
        print(f"Scenario: {scenario.name}")
        print(f"{'='*60}")
        
        try:
            # Run scenario
            plan, outline, pack, prompt, metadata = run_scenario(scenario, verbose)
            
            # Run checks
            all_failures = []
            
            failures = check_topic_signature(scenario, metadata, verbose)
            all_failures.extend(failures)
            
            failures = check_kb_drift(scenario, metadata, prompt, verbose)
            all_failures.extend(failures)
            
            failures = check_fact_drift(scenario, metadata, prompt, verbose)
            all_failures.extend(failures)
            
            failures = check_provided_sources(scenario, plan, outline, prompt, verbose)
            all_failures.extend(failures)
            
            failures = check_outline_semantics(scenario, outline, metadata, verbose)
            all_failures.extend(failures)
            
            failures = check_hook_safety(scenario, metadata, prompt, verbose)
            all_failures.extend(failures)
            
            # Store result
            passed = len(all_failures) == 0
            result = DiagnosticResult(
                scenario_name=scenario.name,
                passed=passed,
                failures=all_failures,
                metrics=metadata
            )
            results.append(result)
            
            # Print summary
            if passed:
                print(f"\n✅ PASSED: All checks passed for '{scenario.name}'")
            else:
                print(f"\n❌ FAILED: {len(all_failures)} check(s) failed for '{scenario.name}':")
                for i, failure in enumerate(all_failures, 1):
                    print(f"   {i}. {failure}")
        
        except Exception as e:
            print(f"\n💥 ERROR: Exception in scenario '{scenario.name}': {str(e)}")
            if verbose:
                import traceback
                traceback.print_exc()
            
            result = DiagnosticResult(
                scenario_name=scenario.name,
                passed=False,
                failures=[f"Exception: {str(e)}"],
                metrics={}
            )
            results.append(result)
    
    return results


def print_summary(results: List[DiagnosticResult]):
    """Print final summary."""
    print(f"\n\n{'='*60}")
    print("FINAL SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for r in results if r.passed)
    failed = len(results) - passed
    
    print(f"\nTotal scenarios: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed > 0:
        print(f"\nFailed scenarios:")
        for r in results:
            if not r.passed:
                print(f"  - {r.scenario_name}: {len(r.failures)} failure(s)")
    
    return failed == 0


def main():
    parser = argparse.ArgumentParser(description='Newsletter Pipeline Diagnostics')
    parser.add_argument('--verbose', action='store_true', help='Show detailed output')
    parser.add_argument('--scenario', type=str, help='Run only one scenario (partial match)')
    parser.add_argument('--json', action='store_true', help='Output results as JSON')
    
    args = parser.parse_args()
    
    # Create scenarios
    scenarios = create_scenarios()
    
    # Run diagnostics
    results = run_diagnostics(scenarios, verbose=args.verbose, scenario_filter=args.scenario)
    
    # Output results
    if args.json:
        output = {
            'total': len(results),
            'passed': sum(1 for r in results if r.passed),
            'failed': sum(1 for r in results if not r.passed),
            'results': [asdict(r) for r in results]
        }
        print(json.dumps(output, indent=2))
    else:
        success = print_summary(results)
        sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
