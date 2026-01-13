#!/usr/bin/env python3
"""
Test the LIVE Grok newsletter generation with debug output.
Run this to see exactly what facts are being retrieved and filtered.
"""
import sys
from newsletter_engine import NewsletterEngine

# Grok outline data
outline_data = {
    'headline': 'Grok is a horror show and Musk is loving it',
    'preview': "Elon Musk's Grok is being used to create non-consensual sexual deepfakes of women in religious clothing. And it is not only being allowed, but promoted.",
    'opening_hook': 'A courtroom-themed sketch: consent missing, platform accountability on trial',
    'main_story': {
        'heading': 'Grok is a horror show and Musk is loving it',
        'target_word_count': 800,
        'key_points': [
            'Grok, Musk\'s LLM, has from the start been largely a vanity project.',
            'In the story, journalist Samantha Cole describes how Grok is being used to create sexually explicit images.',
            'Musk isn\'t doing anything to stop Grok from behaving this way.',
            'The second part of the Times story is about the women being targeted.',
            'A range of people are using Grok to purposefully create images of Muslim women in hijabs.',
            'The mission of Grok is to deal a blow to OpenAI.',
            'The story has also put the issue of deepfakes back on the agenda.',
        ],
    },
    'additional_sections': [],
    'sources': [
        {
            'title': 'Grok Is Being Used to Mock and Strip Women in Hijabs and Saris',
            'url': 'https://www.wired.com/story/grok-is-being-used-to-mock-and-strip-women-in-hijabs-and-sarees/',
        },
        {
            'title': 'X Didn\'t Fix Grok\'s \'Undressing\' Problem',
            'url': 'https://www.wired.com/story/x-didnt-fix-groks-undressing-problem-it-just-makes-people-pay-for-it/',
        },
    ],
}

idea = "The world is already on fire, but we have to talk about Grok and deepfakes"

style_metrics = {
    'western_focus': 0.7,
    'critical_tone': 0.8,
}

story_type_data = {
    'key': 'news_analysis',
    'name': 'News Analysis',
}

print("="*70)
print("🧪 TESTING LIVE GROK NEWSLETTER GENERATION")
print("="*70)
print()

try:
    engine = NewsletterEngine()
    
    print("📝 Building prompt with NEW topic-aware fact retrieval...")
    print()
    
    system_prompt, user_prompt, metadata = engine.generator.build_prompt_from_outline_data(
        outline_data=outline_data,
        idea=idea,
        style_metrics=style_metrics,
        story_type_data=story_type_data
    )
    
    print()
    print("="*70)
    print("✅ PROMPT GENERATED")
    print("="*70)
    print()
    
    # Extract facts section
    if "# FACTS AND DATA TO USE" in user_prompt:
        facts_section = user_prompt.split("# FACTS AND DATA TO USE")[1].split("#")[0]
        print("📋 FACTS IN PROMPT:")
        print(facts_section[:1000])
        
        # Check for irrelevant terms
        irrelevant_terms = ['OpenAI', 'grantwash', 'labor', 'Instagram', 'Mona Lisa', 'college dropout']
        found_irrelevant = []
        for term in irrelevant_terms:
            if term.lower() in facts_section.lower():
                found_irrelevant.append(term)
        
        if found_irrelevant:
            print()
            print(f"❌ WARNING: Found irrelevant terms: {', '.join(found_irrelevant)}")
        else:
            print()
            print("✅ SUCCESS: No irrelevant terms found in facts!")
    
    print()
    print(f"Metadata: {metadata.get('facts_count', 0)} facts, {metadata.get('rag_examples_count', 0)} RAG examples")
    print()
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
