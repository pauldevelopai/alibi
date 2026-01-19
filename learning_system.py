"""
Learning System - Learn from user edits to improve future generations

Stores:
- Original AI-generated outlines
- User's edits and changes
- Final approved versions
- Patterns from successful edits

Uses this data to improve prompts and generation quality.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional

DATA_DIR = Path(__file__).parent / "data"
LEARNINGS_FILE = DATA_DIR / "user_learnings.json"
EDIT_HISTORY_FILE = DATA_DIR / "edit_history.json"


def load_learnings() -> dict:
    """Load accumulated learnings."""
    if not LEARNINGS_FILE.exists():
        return {
            'headline_preferences': [],
            'section_preferences': [],
            'tone_adjustments': [],
            'common_additions': [],
            'rejected_patterns': [],
        }
    with open(LEARNINGS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_learnings(learnings: dict):
    """Save learnings."""
    DATA_DIR.mkdir(exist_ok=True)
    with open(LEARNINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(learnings, f, indent=2, ensure_ascii=False, default=str)


def load_edit_history() -> list:
    """Load edit history."""
    if not EDIT_HISTORY_FILE.exists():
        return []
    with open(EDIT_HISTORY_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_edit_history(history: list):
    """Save edit history."""
    DATA_DIR.mkdir(exist_ok=True)
    with open(EDIT_HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False, default=str)


def record_outline_edit(
    original_outline: dict,
    edited_outline: dict,
    idea: str,
    story_type: str = ""
) -> dict:
    """
    Record an edit to an outline for learning.
    
    Args:
        original_outline: The AI-generated outline
        edited_outline: The user's edited version
        idea: The original idea
        story_type: The story type selected
    
    Returns:
        Summary of what was learned
    """
    history = load_edit_history()
    learnings = load_learnings()
    
    # Create edit record
    edit_record = {
        'timestamp': datetime.now().isoformat(),
        'idea': idea[:200],
        'story_type': story_type,
        'changes': [],
    }
    
    # Compare headlines
    original_headlines = original_outline.get('headline_options', [])
    chosen_headline = edited_outline.get('headline', '')
    
    if chosen_headline and chosen_headline not in original_headlines:
        # User wrote their own headline - this is valuable learning
        edit_record['changes'].append({
            'type': 'custom_headline',
            'original_options': original_headlines,
            'user_wrote': chosen_headline,
        })
        learnings['headline_preferences'].append({
            'context': idea[:100],
            'rejected': original_headlines,
            'preferred': chosen_headline,
            'timestamp': datetime.now().isoformat(),
        })
    elif chosen_headline:
        # User chose from options - note which style
        idx = original_headlines.index(chosen_headline) if chosen_headline in original_headlines else -1
        edit_record['changes'].append({
            'type': 'chose_headline',
            'index': idx,
            'chosen': chosen_headline,
        })
    
    # Compare sections
    original_sections = original_outline.get('sections', [])
    edited_sections = edited_outline.get('sections', [])
    
    for i, (orig, edited) in enumerate(zip(original_sections, edited_sections)):
        # Check if heading was changed
        if orig.get('heading') != edited.get('heading'):
            edit_record['changes'].append({
                'type': 'heading_change',
                'section': i,
                'original': orig.get('heading'),
                'changed_to': edited.get('heading'),
            })
        
        # Check if bullets were added
        orig_bullets = set(orig.get('bullet_points', []))
        edited_bullets = set(edited.get('bullet_points', []))
        
        added_bullets = edited_bullets - orig_bullets
        if added_bullets:
            edit_record['changes'].append({
                'type': 'bullets_added',
                'section': i,
                'added': list(added_bullets),
            })
            learnings['common_additions'].extend(list(added_bullets))
        
        # Check for user notes
        if edited.get('user_notes'):
            edit_record['changes'].append({
                'type': 'user_notes',
                'section': i,
                'notes': edited['user_notes'],
            })
    
    # Check tone changes
    original_tone = original_outline.get('tone_notes', '')
    edited_tone = edited_outline.get('tone_notes', '')
    
    if original_tone != edited_tone and edited_tone:
        edit_record['changes'].append({
            'type': 'tone_adjustment',
            'original': original_tone,
            'adjusted_to': edited_tone,
        })
        learnings['tone_adjustments'].append(edited_tone)
    
    # Save
    history.append(edit_record)
    save_edit_history(history[-100:])  # Keep last 100 edits
    save_learnings(learnings)
    
    return {
        'changes_recorded': len(edit_record['changes']),
        'summary': edit_record,
    }


def get_learning_context() -> str:
    """
    Get learning context to include in generation prompts.
    Returns string to append to prompts based on learned preferences.
    """
    learnings = load_learnings()
    
    context_parts = []
    
    # Headline preferences
    if learnings.get('headline_preferences'):
        recent = learnings['headline_preferences'][-5:]
        context_parts.append("## LEARNED HEADLINE PREFERENCES")
        context_parts.append("The user has previously rejected AI headlines and written their own:")
        for pref in recent:
            context_parts.append(f"- Preferred: \"{pref['preferred']}\"")
        context_parts.append("")
    
    # Tone adjustments
    if learnings.get('tone_adjustments'):
        recent = list(set(learnings['tone_adjustments'][-10:]))
        context_parts.append("## LEARNED TONE PREFERENCES")
        context_parts.append("The user frequently adjusts tone to:")
        for tone in recent[:5]:
            context_parts.append(f"- {tone}")
        context_parts.append("")
    
    # Common additions
    if learnings.get('common_additions'):
        # Find frequently added content
        from collections import Counter
        additions = Counter(learnings['common_additions'])
        common = additions.most_common(5)
        if common:
            context_parts.append("## COMMONLY ADDED CONTENT")
            context_parts.append("The user frequently adds these types of points:")
            for addition, count in common:
                if count >= 2:
                    context_parts.append(f"- {addition[:80]}...")
            context_parts.append("")
    
    return "\n".join(context_parts)


def get_edit_stats() -> dict:
    """Get statistics about user edits."""
    history = load_edit_history()
    learnings = load_learnings()
    
    return {
        'total_edits': len(history),
        'custom_headlines': len(learnings.get('headline_preferences', [])),
        'tone_adjustments': len(learnings.get('tone_adjustments', [])),
        'content_additions': len(learnings.get('common_additions', [])),
    }


# ============================================================================
# Test
# ============================================================================

if __name__ == "__main__":
    print("Learning System Status:")
    stats = get_edit_stats()
    for k, v in stats.items():
        print(f"  {k}: {v}")
    
    print("\nLearning Context:")
    print(get_learning_context() or "  (No learnings yet)")









