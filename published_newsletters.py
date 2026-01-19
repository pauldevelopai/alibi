"""
Published Newsletters - Store finalized newsletters for training

When a newsletter is "published", it gets saved here as training data
that can be used to further fine-tune the model.

Structure:
- Each published newsletter = one training example
- Format: idea/prompt → final newsletter content
- Can be exported for OpenAI fine-tuning
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict

DATA_DIR = Path(__file__).parent / "data"
PUBLISHED_FILE = DATA_DIR / "published_newsletters.json"


def load_published() -> dict:
    """Load published newsletters."""
    if not PUBLISHED_FILE.exists():
        return {
            'newsletters': [],
            'metadata': {
                'total_published': 0,
                'last_published': None,
                'ready_for_training': 0
            }
        }
    try:
        with open(PUBLISHED_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return load_published.__wrapped__()


def save_published(data: dict):
    """Save published newsletters."""
    DATA_DIR.mkdir(exist_ok=True)
    data['metadata']['total_published'] = len(data.get('newsletters', []))
    with open(PUBLISHED_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)


def publish_newsletter(
    idea: str,
    headline: str,
    content: str,
    outline: dict = None,
    story_type: str = "",
    notes: str = ""
) -> dict:
    """
    Publish a newsletter - saves it as training data.
    
    Args:
        idea: The original idea/prompt
        headline: The final headline
        content: The final newsletter content (after any edits)
        outline: The outline used
        story_type: The story type
        notes: Any notes about this newsletter
    
    Returns:
        The published newsletter record
    """
    data = load_published()
    
    # Generate ID
    newsletter_id = hashlib.md5(
        f"{idea}{headline}{datetime.now().isoformat()}".encode()
    ).hexdigest()[:12]
    
    # Create the record
    record = {
        'id': newsletter_id,
        'published_at': datetime.now().isoformat(),
        'idea': idea,
        'headline': headline,
        'content': content,
        'outline': outline,
        'story_type': story_type,
        'notes': notes,
        'word_count': len(content.split()),
        'char_count': len(content),
        'used_for_training': False,
        'training_exported_at': None
    }
    
    data['newsletters'].append(record)
    data['metadata']['last_published'] = datetime.now().isoformat()
    data['metadata']['ready_for_training'] = sum(
        1 for n in data['newsletters'] if not n.get('used_for_training', False)
    )
    
    save_published(data)
    
    return record


def get_published_newsletters(limit: int = None) -> List[dict]:
    """Get published newsletters, most recent first."""
    data = load_published()
    newsletters = data.get('newsletters', [])
    newsletters = sorted(newsletters, key=lambda x: x.get('published_at', ''), reverse=True)
    if limit:
        return newsletters[:limit]
    return newsletters


def get_unpublished_for_training() -> List[dict]:
    """Get newsletters not yet used for training."""
    data = load_published()
    return [n for n in data.get('newsletters', []) if not n.get('used_for_training', False)]


def mark_as_trained(newsletter_ids: List[str]):
    """Mark newsletters as used for training."""
    data = load_published()
    now = datetime.now().isoformat()
    
    for newsletter in data.get('newsletters', []):
        if newsletter.get('id') in newsletter_ids:
            newsletter['used_for_training'] = True
            newsletter['training_exported_at'] = now
    
    data['metadata']['ready_for_training'] = sum(
        1 for n in data['newsletters'] if not n.get('used_for_training', False)
    )
    
    save_published(data)


def export_for_fine_tuning(
    include_already_trained: bool = False,
    output_file: str = None
) -> dict:
    """
    Export published newsletters in OpenAI fine-tuning format.
    
    Format: JSONL with {"messages": [...]} structure
    
    Returns:
        dict with 'file_path', 'count', 'newsletters_exported'
    """
    data = load_published()
    newsletters = data.get('newsletters', [])
    
    if not include_already_trained:
        newsletters = [n for n in newsletters if not n.get('used_for_training', False)]
    
    if not newsletters:
        return {'error': 'No newsletters available for training', 'count': 0}
    
    # Prepare training examples
    training_examples = []
    
    for newsletter in newsletters:
        idea = newsletter.get('idea', '')
        headline = newsletter.get('headline', '')
        content = newsletter.get('content', '')
        
        if not idea or not content:
            continue
        
        # Create the training example
        example = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are Paul McNally, a journalist who writes newsletters about AI and media. Write in a punchy, personal style with short paragraphs, specific examples, and an Africa/Global South perspective."
                },
                {
                    "role": "user",
                    "content": f"Write a newsletter about: {idea}"
                },
                {
                    "role": "assistant",
                    "content": f"# {headline}\n\n{content}"
                }
            ]
        }
        training_examples.append(example)
    
    # Write to file
    if output_file is None:
        output_file = DATA_DIR / f"training_published_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
    else:
        output_file = Path(output_file)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for example in training_examples:
            f.write(json.dumps(example, ensure_ascii=False) + '\n')
    
    # Mark as exported
    exported_ids = [n['id'] for n in newsletters if n.get('id')]
    mark_as_trained(exported_ids)
    
    return {
        'file_path': str(output_file),
        'count': len(training_examples),
        'newsletters_exported': exported_ids
    }


def get_stats() -> dict:
    """Get publishing statistics."""
    data = load_published()
    newsletters = data.get('newsletters', [])
    
    return {
        'total_published': len(newsletters),
        'ready_for_training': sum(1 for n in newsletters if not n.get('used_for_training', False)),
        'already_trained': sum(1 for n in newsletters if n.get('used_for_training', False)),
        'total_words': sum(n.get('word_count', 0) for n in newsletters),
        'last_published': data.get('metadata', {}).get('last_published')
    }


def delete_published(newsletter_id: str) -> bool:
    """Delete a published newsletter."""
    data = load_published()
    original_count = len(data.get('newsletters', []))
    data['newsletters'] = [n for n in data.get('newsletters', []) if n.get('id') != newsletter_id]
    
    if len(data['newsletters']) < original_count:
        save_published(data)
        return True
    return False








