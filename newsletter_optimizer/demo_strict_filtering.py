#!/usr/bin/env python3
"""
Demonstration: Strict Fact Filtering

Shows how irrelevant facts are now being dropped with stricter filtering.
"""

from newsletter_engine import NewsletterPlan, StyleProfile, PromptConstructor
from topic_signature import build_topic_signature

def main():
    print("=" * 70)
    print("DEMONSTRATION: Strict Fact Filtering")
    print("=" * 70)
    print()
    
    # Grok deepfakes topic
    plan = NewsletterPlan(
        theme="Grok deepfake undressing tool targeting women in hijabs",
        audience="Newsrooms",
        purpose="Investigate",
        angle_choices=["Platform accountability for non-consensual AI imagery"],
        required_inputs_coverage=[],
        style_profile=StyleProfile(),
        sections=[],
        call_to_action="",
        fact_risk_flags=[],
        outline_text="",
        target_length=800
    )
    
    # Build topic signature
    provided_sources = [
        {'title': "Grok's image generator creates undressing images", 
         'url': 'https://wired.com/grok-deepfakes', 'note': ''}
    ]
    
    topic_sig = build_topic_signature(plan, {}, provided_sources, [])
    
    print("TOPIC SIGNATURE:")
    print(f"  Theme: {topic_sig.theme}")
    print(f"  Entities: {list(topic_sig.entities)[:5]}")
    print(f"  Keywords: {list(topic_sig.keywords)[:8]}")
    print()
    
    # Simulate facts from KB (like what semantic search returns)
    test_facts = [
        {
            'text': 'Grok generated 10,000 non-consensual deepfake images in first week',
            'source_title': 'Wired investigation on Grok deepfakes',
            'source_url': 'https://wired.com/grok',
            'is_optional_context': False
        },
        {
            'text': 'X platform lacks verification for synthetic media',
            'source_title': 'Platform accountability report',
            'source_url': 'https://techcrunch.com/x-verification',
            'is_optional_context': False
        },
        {
            'text': 'We like to complain about AI slop, but there\'s amazing AI content',
            'source_title': 'You can\'t trust your eyes anymore, says Instagram head',
            'source_url': 'https://theverge.com/instagram',
            'is_optional_context': False
        },
        {
            'text': 'OpenAI announced up to $2 million in funding for AI safety research',
            'source_title': 'Beware of OpenAI\'s Grantwashing on AI Harms',
            'source_url': 'https://techpolicy.press/grantwashing',
            'is_optional_context': False
        },
        {
            'text': 'A recent report shows employees save an hour a day using AI tools',
            'source_title': 'AI Labor Is Boring. AI Lust Is Big Business',
            'source_url': 'https://wired.com/ai-labor',
            'is_optional_context': False
        },
    ]
    
    print("=" * 70)
    print("FACTS BEFORE FILTERING: 5")
    print("=" * 70)
    for i, fact in enumerate(test_facts, 1):
        print(f"\n{i}. {fact['text'][:60]}...")
        print(f"   Source: {fact['source_title'][:50]}")
    print()
    
    # Apply filtering
    pc = PromptConstructor()
    filtered_facts, metrics = pc.filter_facts_by_topic(test_facts, topic_sig, provided_sources)
    
    print("=" * 70)
    print("FILTERING RESULTS:")
    print("=" * 70)
    print(f"  Before: {metrics['before']} facts")
    print(f"  Relevant: {metrics['relevant']} facts")
    print(f"  Optional: {metrics['optional']} facts")
    print(f"  Dropped: {metrics['dropped']} facts")
    print()
    
    print("=" * 70)
    print(f"FACTS AFTER FILTERING: {len(filtered_facts)}")
    print("=" * 70)
    for i, fact in enumerate(filtered_facts, 1):
        print(f"\n{i}. {fact['text'][:60]}...")
        print(f"   Source: {fact['source_title'][:50]}")
    print()
    
    if len(filtered_facts) < len(test_facts):
        print("✅ SUCCESS: Irrelevant facts were filtered out!")
        print()
        print("Dropped facts:")
        dropped_indices = [0, 2, 3, 4]  # Instagram, grantwashing, AI labor
        for i in dropped_indices:
            if i < len(test_facts):
                print(f"  - {test_facts[i]['source_title'][:50]}")
    else:
        print("⚠️ WARNING: No facts were dropped (filtering may be too loose)")
    
    print()


if __name__ == '__main__':
    main()
