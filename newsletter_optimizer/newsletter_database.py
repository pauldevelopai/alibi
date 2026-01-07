"""
Newsletter Database - Save, version, and retrieve generated newsletters

Features:
- Save every generated newsletter with metadata
- Version history for each newsletter (track iterations)
- Search and filter by date, status, topic
- Continue editing from any saved version
- Export to various formats
"""

import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional, List
import hashlib


DATA_DIR = Path(__file__).parent / "data"
NEWSLETTERS_DB_FILE = DATA_DIR / "newsletters_db.json"


# ============================================================================
# Database Operations
# ============================================================================

def load_database() -> dict:
    """Load the newsletters database."""
    if not NEWSLETTERS_DB_FILE.exists():
        return {
            'newsletters': {},  # id -> newsletter data
            'metadata': {
                'created': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat(),
                'total_newsletters': 0,
                'total_versions': 0,
            }
        }
    
    with open(NEWSLETTERS_DB_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_database(db: dict):
    """Save the newsletters database."""
    DATA_DIR.mkdir(exist_ok=True)
    db['metadata']['last_updated'] = datetime.now().isoformat()
    
    with open(NEWSLETTERS_DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=2, ensure_ascii=False, default=str)


def generate_id() -> str:
    """Generate a unique newsletter ID."""
    return str(uuid.uuid4())[:8]


def generate_version_id() -> str:
    """Generate a version ID based on timestamp."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


# ============================================================================
# Newsletter CRUD
# ============================================================================

def create_newsletter(
    idea: str,
    headline: str = "",
    preview: str = "",
    content: str = "",
    outline: dict = None,
    edited_outline: dict = None,
    story_type: str = "",
    sections: list = None,
    metrics: dict = None,
    status: str = "draft",
    tags: list = None,
) -> dict:
    """
    Create a new newsletter entry.
    
    Args:
        idea: The original idea/topic
        headline: The chosen headline
        preview: The preview/subtitle
        content: The generated content (markdown/HTML)
        outline: The AI-generated outline
        edited_outline: The user-edited outline
        story_type: The story type (how-to, news, etc.)
        sections: Selected sections
        metrics: Style metric settings
        status: draft, in_progress, ready, published
        tags: User-defined tags
    
    Returns:
        The created newsletter record
    """
    db = load_database()
    
    newsletter_id = generate_id()
    version_id = generate_version_id()
    now = datetime.now().isoformat()
    
    newsletter = {
        'id': newsletter_id,
        'created_at': now,
        'updated_at': now,
        'idea': idea,
        'headline': headline,
        'preview': preview,
        'story_type': story_type,
        'status': status,
        'tags': tags or [],
        'current_version': version_id,
        'versions': {
            version_id: {
                'version_id': version_id,
                'created_at': now,
                'headline': headline,
                'preview': preview,
                'content': content,
                'outline': outline,
                'edited_outline': edited_outline,
                'sections': sections or [],
                'metrics': metrics or {},
                'notes': 'Initial version',
            }
        }
    }
    
    db['newsletters'][newsletter_id] = newsletter
    db['metadata']['total_newsletters'] += 1
    db['metadata']['total_versions'] += 1
    
    save_database(db)
    
    return newsletter


def save_version(
    newsletter_id: str,
    headline: str = None,
    preview: str = None,
    content: str = None,
    outline: dict = None,
    edited_outline: dict = None,
    sections: list = None,
    metrics: dict = None,
    notes: str = "",
) -> dict:
    """
    Save a new version of an existing newsletter.
    
    Returns:
        The updated newsletter record
    """
    db = load_database()
    
    if newsletter_id not in db['newsletters']:
        raise ValueError(f"Newsletter {newsletter_id} not found")
    
    newsletter = db['newsletters'][newsletter_id]
    version_id = generate_version_id()
    now = datetime.now().isoformat()
    
    # Get current version to carry forward unchanged fields
    current = newsletter['versions'].get(newsletter['current_version'], {})
    
    new_version = {
        'version_id': version_id,
        'created_at': now,
        'headline': headline if headline is not None else current.get('headline', ''),
        'preview': preview if preview is not None else current.get('preview', ''),
        'content': content if content is not None else current.get('content', ''),
        'outline': outline if outline is not None else current.get('outline'),
        'edited_outline': edited_outline if edited_outline is not None else current.get('edited_outline'),
        'sections': sections if sections is not None else current.get('sections', []),
        'metrics': metrics if metrics is not None else current.get('metrics', {}),
        'notes': notes,
        'parent_version': newsletter['current_version'],
    }
    
    newsletter['versions'][version_id] = new_version
    newsletter['current_version'] = version_id
    newsletter['updated_at'] = now
    
    if headline:
        newsletter['headline'] = headline
    if preview:
        newsletter['preview'] = preview
    
    db['metadata']['total_versions'] += 1
    
    save_database(db)
    
    return newsletter


def get_newsletter(newsletter_id: str) -> Optional[dict]:
    """Get a newsletter by ID."""
    db = load_database()
    return db['newsletters'].get(newsletter_id)


def get_version(newsletter_id: str, version_id: str) -> Optional[dict]:
    """Get a specific version of a newsletter."""
    newsletter = get_newsletter(newsletter_id)
    if not newsletter:
        return None
    return newsletter['versions'].get(version_id)


def update_newsletter_metadata(
    newsletter_id: str,
    status: str = None,
    tags: list = None,
    headline: str = None,
    story_type: str = None,
) -> dict:
    """Update newsletter metadata without creating a new version."""
    db = load_database()
    
    if newsletter_id not in db['newsletters']:
        raise ValueError(f"Newsletter {newsletter_id} not found")
    
    newsletter = db['newsletters'][newsletter_id]
    
    if status:
        newsletter['status'] = status
    if tags is not None:
        newsletter['tags'] = tags
    if headline:
        newsletter['headline'] = headline
    if story_type:
        newsletter['story_type'] = story_type
    
    newsletter['updated_at'] = datetime.now().isoformat()
    
    save_database(db)
    
    return newsletter


def update_newsletter_stats(
    newsletter_id: str,
    creation_time_minutes: int = None,
    substack_views: int = None,
    substack_opens: int = None,
    substack_open_rate: float = None,
    substack_clicks: int = None,
    substack_new_subscribers: int = None,
    substack_url: str = None,
    published_date: str = None,
    notes: str = None,
) -> dict:
    """Update newsletter performance stats and creation time tracking."""
    db = load_database()
    
    if newsletter_id not in db['newsletters']:
        raise ValueError(f"Newsletter {newsletter_id} not found")
    
    newsletter = db['newsletters'][newsletter_id]
    
    # Initialize stats dict if not present
    if 'stats' not in newsletter:
        newsletter['stats'] = {}
    
    stats = newsletter['stats']
    
    # Update creation time
    if creation_time_minutes is not None:
        stats['creation_time_minutes'] = creation_time_minutes
    
    # Update Substack metrics
    if substack_views is not None:
        stats['substack_views'] = substack_views
    if substack_opens is not None:
        stats['substack_opens'] = substack_opens
    if substack_open_rate is not None:
        stats['substack_open_rate'] = substack_open_rate
    if substack_clicks is not None:
        stats['substack_clicks'] = substack_clicks
    if substack_new_subscribers is not None:
        stats['substack_new_subscribers'] = substack_new_subscribers
    if substack_url is not None:
        stats['substack_url'] = substack_url
    if published_date is not None:
        stats['published_date'] = published_date
    if notes is not None:
        stats['notes'] = notes
    
    stats['stats_updated_at'] = datetime.now().isoformat()
    newsletter['updated_at'] = datetime.now().isoformat()
    
    save_database(db)
    
    return newsletter


def get_all_newsletter_stats() -> list:
    """Get stats for all newsletters for progress tracking."""
    db = load_database()
    
    stats_list = []
    for nl_id, newsletter in db['newsletters'].items():
        stats = newsletter.get('stats', {})
        stats_list.append({
            'id': nl_id,
            'headline': newsletter.get('headline', 'Untitled'),
            'status': newsletter.get('status', 'draft'),
            'created_at': newsletter.get('created_at', ''),
            'published_date': stats.get('published_date', ''),
            'creation_time_minutes': stats.get('creation_time_minutes', 0),
            'substack_views': stats.get('substack_views', 0),
            'substack_opens': stats.get('substack_opens', 0),
            'substack_open_rate': stats.get('substack_open_rate', 0),
            'substack_clicks': stats.get('substack_clicks', 0),
            'substack_new_subscribers': stats.get('substack_new_subscribers', 0),
            'substack_url': stats.get('substack_url', ''),
            'notes': stats.get('notes', ''),
        })
    
    # Sort by created_at descending
    stats_list.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    return stats_list


def get_performance_learnings() -> str:
    """
    Generate a summary of performance learnings from all published newsletters.
    This is used to inform the model about what works and what doesn't.
    """
    db = load_database()
    
    learnings = []
    high_performers = []
    low_performers = []
    
    for nl_id, newsletter in db['newsletters'].items():
        if newsletter.get('status') != 'published':
            continue
            
        stats = newsletter.get('stats', {})
        headline = newsletter.get('headline', 'Untitled')
        notes = stats.get('notes', '')
        open_rate = stats.get('substack_open_rate', 0)
        views = stats.get('substack_views', 0)
        new_subs = stats.get('substack_new_subscribers', 0)
        
        if open_rate > 50 or new_subs > 10:
            high_performers.append({
                'headline': headline,
                'open_rate': open_rate,
                'views': views,
                'new_subs': new_subs,
                'notes': notes
            })
        elif open_rate > 0 and open_rate < 30:
            low_performers.append({
                'headline': headline,
                'open_rate': open_rate,
                'views': views,
                'notes': notes
            })
        
        if notes:
            learnings.append(f"- {headline}: {notes}")
    
    summary = ""
    
    if high_performers:
        summary += "## HIGH-PERFORMING NEWSLETTERS (learn from these):\n"
        for hp in high_performers[:5]:
            summary += f"- \"{hp['headline']}\" - {hp['open_rate']:.1f}% open rate, {hp['new_subs']} new subscribers\n"
            if hp['notes']:
                summary += f"  Notes: {hp['notes']}\n"
        summary += "\n"
    
    if low_performers:
        summary += "## LOWER-PERFORMING NEWSLETTERS (avoid these patterns):\n"
        for lp in low_performers[:3]:
            summary += f"- \"{lp['headline']}\" - {lp['open_rate']:.1f}% open rate\n"
            if lp['notes']:
                summary += f"  Notes: {lp['notes']}\n"
        summary += "\n"
    
    if learnings:
        summary += "## AUTHOR'S LEARNINGS AND NOTES:\n"
        summary += "\n".join(learnings[:15])
        summary += "\n"
    
    return summary


def delete_newsletter(newsletter_id: str) -> bool:
    """Delete a newsletter and all its versions."""
    db = load_database()
    
    if newsletter_id not in db['newsletters']:
        return False
    
    versions_count = len(db['newsletters'][newsletter_id]['versions'])
    del db['newsletters'][newsletter_id]
    
    db['metadata']['total_newsletters'] -= 1
    db['metadata']['total_versions'] -= versions_count
    
    save_database(db)
    
    return True


# ============================================================================
# Query & Search
# ============================================================================

def list_newsletters(
    status: str = None,
    story_type: str = None,
    tag: str = None,
    search: str = None,
    limit: int = 50,
    sort_by: str = 'updated_at',
    sort_desc: bool = True,
) -> List[dict]:
    """
    List newsletters with optional filters.
    
    Args:
        status: Filter by status (draft, in_progress, ready, published)
        story_type: Filter by story type
        tag: Filter by tag
        search: Search in headline and idea
        limit: Max results
        sort_by: Field to sort by (created_at, updated_at, headline)
        sort_desc: Sort descending
    
    Returns:
        List of newsletter summaries (without full version history)
    """
    db = load_database()
    
    results = []
    
    for newsletter in db['newsletters'].values():
        # Apply filters
        if status and newsletter.get('status') != status:
            continue
        if story_type and newsletter.get('story_type') != story_type:
            continue
        if tag and tag not in newsletter.get('tags', []):
            continue
        if search:
            search_lower = search.lower()
            if (search_lower not in newsletter.get('headline', '').lower() and
                search_lower not in newsletter.get('idea', '').lower()):
                continue
        
        # Create summary (without full version history)
        current_version = newsletter['versions'].get(newsletter['current_version'], {})
        
        # Determine content stage
        has_content = bool(current_version.get('content', '').strip())
        has_outline = bool(current_version.get('outline') or current_version.get('edited_outline'))
        
        if has_content:
            content_stage = 'complete'
        elif has_outline:
            content_stage = 'outline'
        else:
            content_stage = 'idea'
        
        summary = {
            'id': newsletter['id'],
            'headline': newsletter.get('headline', '') or current_version.get('headline', 'Untitled'),
            'preview': newsletter.get('preview', '') or current_version.get('preview', ''),
            'idea': newsletter.get('idea', '')[:100] + ('...' if len(newsletter.get('idea', '')) > 100 else ''),
            'status': newsletter.get('status', 'draft'),
            'story_type': newsletter.get('story_type', ''),
            'tags': newsletter.get('tags', []),
            'created_at': newsletter.get('created_at', ''),
            'updated_at': newsletter.get('updated_at', ''),
            'version_count': len(newsletter.get('versions', {})),
            'current_version': newsletter.get('current_version', ''),
            'content_stage': content_stage,  # 'idea', 'outline', or 'complete'
        }
        
        results.append(summary)
    
    # Sort
    reverse = sort_desc
    if sort_by in ['created_at', 'updated_at']:
        results.sort(key=lambda x: x.get(sort_by, ''), reverse=reverse)
    elif sort_by == 'headline':
        results.sort(key=lambda x: x.get('headline', '').lower(), reverse=reverse)
    
    return results[:limit]


def get_recent_newsletters(limit: int = 10) -> List[dict]:
    """Get the most recently updated newsletters."""
    return list_newsletters(limit=limit, sort_by='updated_at', sort_desc=True)


def get_drafts() -> List[dict]:
    """Get all draft newsletters."""
    return list_newsletters(status='draft')


def get_stats() -> dict:
    """Get database statistics."""
    db = load_database()
    
    newsletters = list(db['newsletters'].values())
    
    status_counts = {}
    type_counts = {}
    
    for n in newsletters:
        status = n.get('status', 'draft')
        status_counts[status] = status_counts.get(status, 0) + 1
        
        stype = n.get('story_type', 'unclassified')
        type_counts[stype] = type_counts.get(stype, 0) + 1
    
    return {
        'total_newsletters': len(newsletters),
        'total_versions': db['metadata'].get('total_versions', 0),
        'by_status': status_counts,
        'by_type': type_counts,
        'last_updated': db['metadata'].get('last_updated', ''),
    }


# ============================================================================
# Export
# ============================================================================

def export_newsletter_markdown(newsletter_id: str, version_id: str = None) -> str:
    """Export a newsletter version as markdown."""
    newsletter = get_newsletter(newsletter_id)
    if not newsletter:
        return ""
    
    vid = version_id or newsletter['current_version']
    version = newsletter['versions'].get(vid, {})
    
    output = f"""# {version.get('headline', 'Untitled')}

*{version.get('preview', '')}*

---

{version.get('content', '')}

---

*Generated: {version.get('created_at', '')}*
*Version: {vid}*
"""
    
    return output


def export_newsletter_html(newsletter_id: str, version_id: str = None) -> str:
    """Export a newsletter version as HTML."""
    import re
    
    newsletter = get_newsletter(newsletter_id)
    if not newsletter:
        return ""
    
    vid = version_id or newsletter['current_version']
    version = newsletter['versions'].get(vid, {})
    
    content = version.get('content', '')
    
    # Basic markdown to HTML conversion
    content = re.sub(r'^# (.+)$', r'<h1>\1</h1>', content, flags=re.MULTILINE)
    content = re.sub(r'^## (.+)$', r'<h2>\1</h2>', content, flags=re.MULTILINE)
    content = re.sub(r'^### (.+)$', r'<h3>\1</h3>', content, flags=re.MULTILINE)
    content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)
    content = re.sub(r'\*(.+?)\*', r'<em>\1</em>', content)
    content = re.sub(r'\n\n', r'</p><p>', content)
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{version.get('headline', 'Newsletter')}</title>
    <style>
        body {{ font-family: Georgia, serif; max-width: 680px; margin: 0 auto; padding: 20px; }}
        h1 {{ font-size: 2em; }}
        h2 {{ font-size: 1.5em; color: #333; }}
        p {{ line-height: 1.6; }}
    </style>
</head>
<body>
    <h1>{version.get('headline', 'Untitled')}</h1>
    <p><em>{version.get('preview', '')}</em></p>
    <hr>
    <p>{content}</p>
</body>
</html>
"""
    
    return html


# ============================================================================
# Test
# ============================================================================

if __name__ == "__main__":
    print("Newsletter Database Test")
    print("=" * 50)
    
    stats = get_stats()
    print(f"\nDatabase Stats:")
    print(f"  Total newsletters: {stats['total_newsletters']}")
    print(f"  Total versions: {stats['total_versions']}")
    print(f"  By status: {stats['by_status']}")
    
    recent = get_recent_newsletters(5)
    if recent:
        print(f"\nRecent Newsletters:")
        for n in recent:
            print(f"  [{n['id']}] {n['headline'][:50]}... ({n['status']})")
    else:
        print("\nNo newsletters saved yet.")
    
    print("\n" + "=" * 50)
    print("Database ready!")

