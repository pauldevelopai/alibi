"""
Content Inbox - Collect and process AI news for idea generation

Provides:
- Store forwarded emails/newsletters
- Parse and extract key content
- Summarize and tag content
- Feed into idea generation
"""

import os
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional
import re

from dotenv import load_dotenv
from openai import OpenAI
from bs4 import BeautifulSoup

load_dotenv()

# OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Try to import fine-tuning to get the active model
try:
    from fine_tuning import get_active_fine_tuned_model
    FINE_TUNING_AVAILABLE = True
except ImportError:
    FINE_TUNING_AVAILABLE = False
    def get_active_fine_tuned_model():
        return None

# Try to import news fetcher for automatic news when inbox is empty
try:
    from news_fetcher import fetch_all_news, get_recent_ai_news, search_news
    NEWS_FETCHER_AVAILABLE = True
except ImportError:
    NEWS_FETCHER_AVAILABLE = False
    def fetch_all_news(*args, **kwargs):
        return []
    def get_recent_ai_news(*args, **kwargs):
        return []
    def search_news(*args, **kwargs):
        return []

# Try to import usage logging
try:
    from openai_dashboard import log_api_call
    USAGE_LOGGING_AVAILABLE = True
except ImportError:
    USAGE_LOGGING_AVAILABLE = False
    def log_api_call(*args, **kwargs):
        pass

# Try to import knowledge base for curated content
try:
    from knowledge_base import get_knowledge_context, get_articles, add_article as kb_add_article
    KNOWLEDGE_BASE_AVAILABLE = True
except ImportError:
    KNOWLEDGE_BASE_AVAILABLE = False
    def get_knowledge_context(*args, **kwargs):
        return ""
    def get_articles(*args, **kwargs):
        return []
    def kb_add_article(*args, **kwargs):
        return None

def get_model_for_ideas() -> str:
    """Get the best model for idea generation - prefers fine-tuned if available."""
    if FINE_TUNING_AVAILABLE:
        fine_tuned = get_active_fine_tuned_model()
        if fine_tuned:
            return fine_tuned
    return "gpt-4.1"

# Data storage
DATA_DIR = Path(__file__).parent / "data"
INBOX_FILE = DATA_DIR / "content_inbox.json"
SAVED_IDEAS_FILE = DATA_DIR / "saved_ideas.json"


# ============================================================================
# Auto-save Ideas and Sources
# ============================================================================

def load_saved_ideas() -> list:
    """Load all saved ideas from disk."""
    if not SAVED_IDEAS_FILE.exists():
        return []
    try:
        with open(SAVED_IDEAS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []


def save_ideas_to_disk(ideas: list):
    """Save ideas list to disk."""
    DATA_DIR.mkdir(exist_ok=True)
    with open(SAVED_IDEAS_FILE, 'w', encoding='utf-8') as f:
        json.dump(ideas, f, indent=2, ensure_ascii=False, default=str)


def auto_save_generated_ideas(new_ideas: list) -> dict:
    """
    Automatically save generated ideas and add their sources to knowledge base.
    
    Returns stats about what was saved.
    """
    if not new_ideas:
        return {'ideas_saved': 0, 'sources_added': 0}
    
    existing_ideas = load_saved_ideas()
    existing_titles = {i.get('title', '').lower() for i in existing_ideas}
    
    ideas_saved = 0
    sources_added = 0
    sources_seen = set()  # Track URLs to avoid duplicates
    
    for idea in new_ideas:
        # Skip if we already have this idea (by title)
        title = idea.get('title', '')
        if title.lower() in existing_titles:
            continue
        
        # Add metadata
        idea['id'] = f"idea_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{ideas_saved}"
        idea['saved_at'] = datetime.now().isoformat()
        idea['used'] = False
        idea['auto_saved'] = True  # Mark as auto-saved
        
        existing_ideas.append(idea)
        existing_titles.add(title.lower())
        ideas_saved += 1
        
        # Add sources to knowledge base
        sources = idea.get('sources', [])
        for source in sources:
            if isinstance(source, dict):
                url = source.get('url', '')
                if url and url not in sources_seen and url.startswith('http'):
                    sources_seen.add(url)
                    
                    # Add to knowledge base
                    if KNOWLEDGE_BASE_AVAILABLE:
                        try:
                            kb_add_article(
                                title=source.get('title', 'Untitled'),
                                url=url,
                                source=source.get('publication', 'Unknown'),
                                summary='',
                                published=source.get('date', ''),
                                category='idea_source'
                            )
                            sources_added += 1
                        except Exception as e:
                            pass  # Skip if already exists or error
    
    # Save updated ideas
    save_ideas_to_disk(existing_ideas)
    
    return {
        'ideas_saved': ideas_saved,
        'sources_added': sources_added,
        'total_ideas': len(existing_ideas)
    }


# ============================================================================
# Content Storage
# ============================================================================

def load_inbox() -> list[dict]:
    """Load all inbox items."""
    if not INBOX_FILE.exists():
        return []
    with open(INBOX_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_inbox(items: list[dict]):
    """Save inbox items."""
    DATA_DIR.mkdir(exist_ok=True)
    with open(INBOX_FILE, 'w', encoding='utf-8') as f:
        json.dump(items, f, indent=2, ensure_ascii=False, default=str)


def generate_content_id(content: str) -> str:
    """Generate a unique ID for content based on hash."""
    return hashlib.md5(content.encode()).hexdigest()[:12]


def add_to_inbox(
    content: str,
    source: str = "manual",
    title: str = "",
    sender: str = "",
    tags: list[str] = None,
    content_type: str = "newsletter"
) -> dict:
    """
    Add content to the inbox.
    
    Args:
        content: The raw content (text or HTML)
        source: Where it came from (manual, email, url)
        title: Title/subject if known
        sender: Sender/author if known
        tags: Optional tags
        content_type: newsletter, article, tweet, etc.
    
    Returns:
        The created inbox item
    """
    items = load_inbox()
    
    # Clean HTML if present
    if '<' in content and '>' in content:
        soup = BeautifulSoup(content, 'lxml')
        clean_text = soup.get_text(separator='\n', strip=True)
    else:
        clean_text = content
    
    # Generate ID
    content_id = generate_content_id(clean_text)
    
    # Check for duplicates
    for item in items:
        if item.get('id') == content_id:
            return {'error': 'Content already exists in inbox', 'id': content_id}
    
    # Create item
    item = {
        'id': content_id,
        'title': title or extract_title(clean_text),
        'content': clean_text[:10000],  # Limit size
        'source': source,
        'sender': sender,
        'content_type': content_type,
        'tags': tags or [],
        'added_at': datetime.now().isoformat(),
        'used': False,
        'summary': None,
        'key_points': None,
    }
    
    items.append(item)
    save_inbox(items)
    
    return item


def extract_title(text: str) -> str:
    """Extract a title from text content."""
    # Get first non-empty line
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    if lines:
        first_line = lines[0][:100]
        return first_line
    return "Untitled"


def remove_from_inbox(content_id: str) -> bool:
    """Remove an item from inbox."""
    items = load_inbox()
    items = [i for i in items if i.get('id') != content_id]
    save_inbox(items)
    return True


def mark_as_used(content_id: str) -> bool:
    """Mark an inbox item as used."""
    items = load_inbox()
    for item in items:
        if item.get('id') == content_id:
            item['used'] = True
            item['used_at'] = datetime.now().isoformat()
    save_inbox(items)
    return True


def clear_inbox() -> int:
    """Clear all inbox items. Returns count deleted."""
    items = load_inbox()
    count = len(items)
    save_inbox([])
    return count


def get_inbox_stats() -> dict:
    """Get inbox statistics."""
    items = load_inbox()
    return {
        'total': len(items),
        'unused': len([i for i in items if not i.get('used')]),
        'used': len([i for i in items if i.get('used')]),
        'by_type': {},
        'by_source': {},
    }


# ============================================================================
# AI Processing
# ============================================================================

def summarize_content(content_id: str) -> dict:
    """
    Use AI to summarize and extract key points from inbox content.
    """
    items = load_inbox()
    item = next((i for i in items if i.get('id') == content_id), None)
    
    if not item:
        return {'error': 'Item not found'}
    
    if item.get('summary'):
        return {'summary': item['summary'], 'key_points': item.get('key_points', [])}
    
    if not os.getenv("OPENAI_API_KEY"):
        return {'error': 'OpenAI API key not configured'}
    
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system",
                    "content": """You are an AI news analyst helping a journalist who writes about AI and media.
Summarize the content and extract key points that could be relevant for a newsletter.

Return JSON with:
{
    "summary": "2-3 sentence summary",
    "key_points": ["point 1", "point 2", "point 3"],
    "potential_angles": ["angle 1", "angle 2"],
    "tags": ["ai", "media", etc]
}"""
                },
                {
                    "role": "user",
                    "content": f"Title: {item.get('title', 'Unknown')}\n\nContent:\n{item.get('content', '')[:4000]}"
                }
            ],
            temperature=0.3,
            max_tokens=500,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Update item
        item['summary'] = result.get('summary', '')
        item['key_points'] = result.get('key_points', [])
        item['potential_angles'] = result.get('potential_angles', [])
        item['ai_tags'] = result.get('tags', [])
        
        save_inbox(items)
        
        return result
        
    except Exception as e:
        return {'error': f'Summarization failed: {str(e)}'}


def load_newsletter_bible() -> dict:
    """Load the Newsletter Bible for context."""
    bible_file = DATA_DIR / "newsletter_bible.json"
    if not bible_file.exists():
        return {}
    with open(bible_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_past_newsletters_summary() -> str:
    """Load a summary of past newsletters for context."""
    raw_file = DATA_DIR / "newsletters_raw.jsonl"
    if not raw_file.exists():
        return ""
    
    summaries = []
    with open(raw_file, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= 20:  # Limit to 20 most recent
                break
            try:
                nl = json.loads(line)
                title = nl.get('title', '')
                if title:
                    summaries.append(f"- {title}")
            except:
                pass
    
    return "\n".join(summaries)


def generate_ideas_from_inbox(
    story_type: str = "",
    additional_context: str = "",
    max_items: int = 10,
    use_bible: bool = True
) -> dict:
    """
    Generate newsletter ideas based on inbox content AND the Newsletter Bible.
    
    Args:
        story_type: Preferred story type (how_to, news_analysis, etc.)
        additional_context: Additional instructions
        max_items: Max inbox items to consider
        use_bible: Whether to include Newsletter Bible context
    
    Returns:
        dict with 'ideas' list
    """
    items = load_inbox()
    
    # Get unused items first, then recently used
    unused = [i for i in items if not i.get('used')]
    recent = sorted(items, key=lambda x: x.get('added_at', ''), reverse=True)
    
    # Combine, prioritizing unused
    to_use = unused[:max_items]
    if len(to_use) < max_items:
        for item in recent:
            if item not in to_use:
                to_use.append(item)
                if len(to_use) >= max_items:
                    break
    
    # Can generate ideas from Bible even without inbox content
    has_inbox = len(to_use) > 0
    
    if not os.getenv("OPENAI_API_KEY"):
        return {'error': 'OpenAI API key not configured', 'ideas': []}
    
    # Build context from multiple sources
    inbox_context = ""
    sources_used = []
    
    # 1. ALWAYS fetch recent news first (this is the primary source for fresh ideas)
    if NEWS_FETCHER_AVAILABLE:
        try:
            recent_news = get_recent_ai_news(days=7)  # Last 7 days for more variety
            if recent_news:
                inbox_context = "## RECENT AI NEWS (from RSS feeds - last 7 days)\n\n"
                inbox_context += "*Use these URLs as sources in your ideas - they are verified working links.*\n\n"
                for article in recent_news[:15]:  # More articles for variety
                    inbox_context += f"### {article.get('title', 'Untitled')}\n"
                    inbox_context += f"**Source:** {article.get('source', 'Unknown')}\n"
                    url = article.get('url', article.get('link', ''))
                    if url:
                        inbox_context += f"**URL:** {url}\n"
                    if article.get('summary'):
                        inbox_context += f"**Summary:** {article['summary'][:300]}\n"
                    pub_date = article.get('published', article.get('date', ''))
                    if pub_date:
                        inbox_context += f"**Date:** {pub_date}\n"
                    inbox_context += "\n---\n\n"
                has_inbox = True
                sources_used.append(f"RSS News ({len(recent_news[:15])} articles)")
        except Exception as e:
            pass
    
    # 2. Add Knowledge Base articles (curated content)
    if KNOWLEDGE_BASE_AVAILABLE:
        kb_context = get_knowledge_context(max_articles=10, max_chars=4000)
        if kb_context:
            inbox_context += "\n" + kb_context
            has_inbox = True
            sources_used.append("Knowledge Base")
    
    # 3. Add inbox items if available
    if len(to_use) > 0:
        inbox_context += "\n## ADDITIONAL CONTENT FROM INBOX\n\n"
        for item in to_use:
            inbox_context += f"### {item.get('title', 'Untitled')}\n"
            inbox_context += f"**Source:** {item.get('sender', item.get('source', 'Unknown'))}\n"
            url = item.get('url', item.get('link', ''))
            if url:
                inbox_context += f"**URL:** {url}\n"
            if item.get('summary'):
                inbox_context += f"**Summary:** {item['summary']}\n"
            else:
                inbox_context += f"**Content:** {item.get('content', '')[:500]}...\n"
            inbox_context += "\n---\n\n"
        has_inbox = True
        sources_used.append(f"Inbox ({len(to_use)} items)")
    
    # Build context from Newsletter Bible
    bible_context = ""
    if use_bible:
        bible = load_newsletter_bible()
        if bible:
            bible_context = "## YOUR NEWSLETTER PATTERNS (from past successful newsletters)\n\n"
            
            # Top performing topics
            topics = bible.get('topic_strategy', {}).get('primary_themes', [])
            if topics:
                bible_context += f"**Topics that resonate:** {', '.join(topics[:8])}\n\n"
            
            # Headline formulas that work
            patterns = bible.get('headline_formulas', {}).get('pattern_breakdown', {})
            if patterns:
                bible_context += "**Headline patterns that work:**\n"
                for pattern, data in list(patterns.items())[:5]:
                    if data.get('examples'):
                        bible_context += f"- {pattern}: e.g., \"{data['examples'][0]}\"\n"
                bible_context += "\n"
            
            # Performance insights
            perf = bible.get('performance_correlations', {})
            if perf:
                high_perf = perf.get('high_performers', {})
                if high_perf.get('common_elements'):
                    bible_context += f"**What drives high open rates:** {', '.join(high_perf['common_elements'][:5])}\n\n"
            
            # Past newsletter titles for inspiration
            past_titles = load_past_newsletters_summary()
            if past_titles:
                bible_context += "**Your recent newsletter titles (for reference):**\n"
                bible_context += past_titles + "\n\n"
            
            # Rules for success
            rules = bible.get('rules_for_success', [])
            if rules:
                bible_context += "**Your success rules:**\n"
                for rule in rules[:5]:
                    bible_context += f"- {rule}\n"
                bible_context += "\n"
    
    # Build the system prompt - simplified for better JSON generation
    system_prompt = """You are Paul McNally's idea generator for "Develop AI" newsletter (AI for journalists/media professionals).

Generate EXACTLY 5-7 newsletter ideas. Each idea MUST include source URLs from the news provided.

Return this JSON structure:
{
    "ideas": [
        {
            "title": "Provocative headline with question or strong angle",
            "story_type": "news_analysis|how_to|opinion|africa_focused|warning|future",
            "summary": "2-3 sentence description of the angle",
            "sources": [
                {
                    "title": "Article headline",
                    "url": "https://full-url-from-news",
                    "publication": "Publication name",
                    "date": "2025-12-31 or the actual date from the article"
                }
            ],
            "search_query": "Google search to find more sources",
            "angle": "The unique hook that makes this newsletter-worthy",
            "why_it_works": "Specific reason - e.g. 'Taps into media industry concerns about AI replacing jobs' or 'Provocative question headline that performed well in past newsletters'",
            "sections": ["Main Story", "Tools & Tips", "Develop AI Update"]
        }
    ]
}

CRITICAL RULES:
- Generate 5-7 ideas (MINIMUM 5)
- ONLY use URLs that appear in the news provided above - NEVER fabricate URLs
- If a source URL is not explicitly provided in the news above, DO NOT include it
- NEVER use example.com, placeholder URLs, or made-up URLs
- If you don't have a real URL from the news, set sources to an empty array []
- ALWAYS include the publication date for each source (from the news provided)
- Include Africa/Global South angle when possible
- Headlines should be provocative but honest
- why_it_works must be SPECIFIC (not generic like "fits Paul's style")
- Mix story types for variety

⚠️ ANTI-FABRICATION: Every source URL MUST come directly from the news content above. If you cannot find a real URL for an idea, leave sources empty - the user will find their own sources."""
    
    # Build user prompt
    user_prompt = ""
    if inbox_context:
        user_prompt += inbox_context + "\n"
    if bible_context:
        user_prompt += bible_context + "\n"
    
    if not inbox_context and not bible_context:
        return {'error': 'No content in inbox and no Newsletter Bible found', 'ideas': []}
    
    user_prompt += f"""
Preferred story type: {story_type or 'Any'}

Additional context: {additional_context or 'None'}

Generate newsletter ideas based on the current news AND your proven patterns:"""
    
    try:
        # Use fine-tuned model if available
        model = get_model_for_ideas()
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.8,
            max_tokens=3000,
            response_format={"type": "json_object"}
        )
        
        # Log API usage
        usage = response.usage
        if usage and USAGE_LOGGING_AVAILABLE:
            log_api_call(
                model=model,
                feature="idea_generation",
                input_tokens=usage.prompt_tokens,
                output_tokens=usage.completion_tokens
            )
        
        result = json.loads(response.choices[0].message.content)
        
        # CRITICAL: Filter out fake/placeholder URLs from sources
        ideas = result.get('ideas', [])
        for idea in ideas:
            if 'sources' in idea and idea['sources']:
                # Filter out fake URLs
                real_sources = []
                for source in idea['sources']:
                    if isinstance(source, dict):
                        url = source.get('url', '')
                        # Reject placeholder/fake URLs
                        if url and not any(fake in url.lower() for fake in [
                            'example.com', 'placeholder', 'dummy', 'fake',
                            'test.com', 'sample.com', 'lorem', 'xyz.com'
                        ]):
                            # Must start with http
                            if url.startswith('http'):
                                real_sources.append(source)
                idea['sources'] = real_sources
        
        # Check if knowledge base was used
        used_kb = KNOWLEDGE_BASE_AVAILABLE and len(get_articles(limit=1)) > 0
        
        # AUTO-SAVE: Store ideas and add sources to knowledge base
        save_stats = auto_save_generated_ideas(ideas)
        
        return {
            'ideas': ideas,
            'source_count': len(to_use),
            'sources_used': sources_used,
            'used_bible': bool(bible_context),
            'used_inbox': bool(inbox_context),
            'used_knowledge_base': used_kb,
            'model_used': model,
            'auto_saved': save_stats,  # Stats about what was auto-saved
        }
        
    except Exception as e:
        return {'error': f'Idea generation failed: {str(e)}', 'ideas': []}


# ============================================================================
# Email Parsing (for forwarded emails)
# ============================================================================

def parse_forwarded_email(email_content: str) -> dict:
    """
    Parse a forwarded email to extract the original content.
    Handles common forwarding formats.
    """
    content = email_content
    
    # Common forwarding patterns
    forward_patterns = [
        r'---------- Forwarded message ---------',
        r'-------- Original Message --------',
        r'Begin forwarded message:',
        r'From:.*\nSent:.*\nTo:.*\nSubject:',
        r'On .* wrote:',
    ]
    
    # Try to find where the forwarded content starts
    for pattern in forward_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            # Content after the forward marker
            content = content[match.end():].strip()
            break
    
    # Extract sender
    sender_match = re.search(r'From:\s*(.+?)(?:\n|<)', email_content, re.IGNORECASE)
    sender = sender_match.group(1).strip() if sender_match else ""
    
    # Extract subject
    subject_match = re.search(r'Subject:\s*(.+?)(?:\n)', email_content, re.IGNORECASE)
    subject = subject_match.group(1).strip() if subject_match else ""
    
    return {
        'content': content,
        'sender': sender,
        'subject': subject,
    }


# ============================================================================
# Test
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("CONTENT INBOX TEST")
    print("=" * 60)
    
    # Test adding content
    test_content = """
    The Future of AI in African Newsrooms
    
    A new report from the Reuters Institute highlights how 
    African media organizations are adopting AI tools for 
    content creation, fact-checking, and audience engagement.
    
    Key findings:
    - 45% of African newsrooms are experimenting with AI
    - Translation tools are the most common use case
    - Concerns about job displacement remain high
    """
    
    result = add_to_inbox(
        content=test_content,
        source="manual",
        title="Reuters: AI in African Newsrooms",
        sender="Reuters Institute",
        content_type="newsletter"
    )
    
    print(f"\nAdded to inbox: {result.get('id', result.get('error'))}")
    
    # Get stats
    stats = get_inbox_stats()
    print(f"\nInbox stats: {stats}")
    
    # List items
    items = load_inbox()
    print(f"\nInbox items ({len(items)}):")
    for item in items[:5]:
        print(f"  - {item['title'][:50]}... ({item['source']})")

