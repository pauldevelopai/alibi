#!/usr/bin/env python3
"""
Demo script to verify evidence-pack wiring in prompt construction.

This script builds a prompt from a minimal outline + provided sources
and verifies that:
1. RELEVANCE BRIEF section is present (if constructed)
2. EVIDENCE PACK section is present
3. Evidence IDs appear with bracket format like [PS_1]
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from newsletter_engine import PromptConstructor


def main():
    print("=" * 70)
    print("EVIDENCE PACK WIRING DEMO")
    print("=" * 70)
    print()
    
    # Create minimal outline
    outline = """# AI Tools for African Newsrooms

*How to use ChatGPT and Claude for journalism*

## Main Story: Getting Started with AI
Target: 500 words

Key Points:
- AI tools are now accessible to African journalists
- Practical applications in news gathering
- Cost considerations for newsrooms
"""
    
    # Create minimal provided sources
    outline_sources = [
        {
            'title': 'AI Adoption in African Media',
            'url': 'https://example.com/ai-africa-media',
            'publication': 'Tech Africa News',
            'summary': 'African newsrooms are increasingly adopting AI tools for content creation and fact-checking.'
        },
        {
            'title': 'ChatGPT for Journalists Guide',
            'url': 'https://example.com/chatgpt-journalists',
            'publication': 'Media Lab',
            'summary': 'A comprehensive guide on using ChatGPT in journalism workflows.'
        }
    ]
    
    # Create outline struct (minimal)
    outline_struct = {
        'headline': 'AI Tools for African Newsrooms',
        'preview': 'How to use ChatGPT and Claude for journalism',
        'main_story': {
            'heading': 'Getting Started with AI',
            'key_points': [
                'AI tools are now accessible to African journalists',
                'Practical applications in news gathering',
                'Cost considerations for newsrooms'
            ],
            'target_word_count': 500
        },
        'additional_sections': []
    }
    
    # Build prompt using PromptConstructor
    print("Building prompt with PromptConstructor...")
    print(f"  Outline length: {len(outline)} chars")
    print(f"  Provided sources: {len(outline_sources)}")
    print()
    
    constructor = PromptConstructor()
    
    try:
        system_prompt, user_prompt, metadata = constructor.build_prompt(
            outline=outline,
            target_length=500,
            outline_sources=outline_sources,
            style_metrics={},
            outline_struct=outline_struct
        )
        
        print("✅ Prompt built successfully!")
        print()
        
        # Check for RELEVANCE BRIEF
        has_relevance_brief = "# RELEVANCE BRIEF" in user_prompt
        print(f"{'✅' if has_relevance_brief else '❌'} RELEVANCE BRIEF section present: {has_relevance_brief}")
        
        # Check for EVIDENCE PACK
        has_evidence_pack = "# EVIDENCE PACK" in user_prompt
        print(f"{'✅' if has_evidence_pack else '❌'} EVIDENCE PACK section present: {has_evidence_pack}")
        
        # Check for bracketed IDs
        has_ps_1 = "[PS_1]" in user_prompt
        has_ps_2 = "[PS_2]" in user_prompt
        print(f"{'✅' if has_ps_1 else '❌'} Evidence ID [PS_1] found: {has_ps_1}")
        print(f"{'✅' if has_ps_2 else '❌'} Evidence ID [PS_2] found: {has_ps_2}")
        
        # Check metadata
        print()
        print("Metadata checks:")
        has_retrieval_pack = 'retrieval_pack' in metadata
        has_evidence_ids = 'evidence_ids' in metadata
        print(f"{'✅' if has_retrieval_pack else '❌'} metadata['retrieval_pack'] present: {has_retrieval_pack}")
        print(f"{'✅' if has_evidence_ids else '❌'} metadata['evidence_ids'] present: {has_evidence_ids}")
        
        if has_evidence_ids:
            evidence_ids = metadata.get('evidence_ids', [])
            print(f"  Evidence IDs count: {len(evidence_ids)}")
            if evidence_ids:
                print(f"  Sample IDs: {evidence_ids[:3]}")
        
        # Print sample of EVIDENCE PACK section
        if has_evidence_pack:
            print()
            print("Sample from EVIDENCE PACK section:")
            print("-" * 70)
            # Find and extract EVIDENCE PACK section
            start = user_prompt.find("# EVIDENCE PACK")
            end = user_prompt.find("\n# ", start + 1)
            if end == -1:
                end = start + 500  # Just show first 500 chars if no next section
            evidence_section = user_prompt[start:end]
            print(evidence_section[:600])
            if len(evidence_section) > 600:
                print("...")
            print("-" * 70)
        
        print()
        print("=" * 70)
        print("DEMO COMPLETE")
        print("=" * 70)
        
        # Summary
        all_checks_pass = (
            has_evidence_pack and 
            (has_ps_1 or has_ps_2) and 
            has_retrieval_pack and 
            has_evidence_ids
        )
        
        if all_checks_pass:
            print("✅ ALL CHECKS PASSED - Evidence pack wiring is working correctly!")
            return 0
        else:
            print("⚠️  SOME CHECKS FAILED - Review output above")
            return 1
            
    except Exception as e:
        print(f"❌ Error building prompt: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
