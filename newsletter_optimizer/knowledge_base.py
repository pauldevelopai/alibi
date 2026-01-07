"""
Knowledge Base - Store and retrieve AI news/content for newsletter research

This is SEPARATE from the fine-tuned model:
- Fine-tuned model = HOW you write (style, voice, tone)
- Knowledge Base = WHAT you write about (facts, news, context)

The knowledge base stores:
- Curated news articles (selected by user)
- STRUCTURED FACTS: statistics, quotes, claims with citations
- Source URLs for citation
- Manually uploaded PDFs and reports

NEW: Automatic fact extraction and relevance matching
- When articles are added, AI extracts structured facts
- When generating, only RELEVANT facts are automatically injected
- Each fact carries its citation for inline linking

It does NOT affect writing style - only provides factual content.
"""

import json
import hashlib
import re
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple
import requests
from bs4 import BeautifulSoup

# OpenAI for fact extraction
try:
    from openai import OpenAI
    from dotenv import load_dotenv
    load_dotenv()
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai_client = None

DATA_DIR = Path(__file__).parent / "data"
KNOWLEDGE_BASE_FILE = DATA_DIR / "knowledge_base.json"
FACTS_FILE = DATA_DIR / "extracted_facts.json"  # Separate file for structured facts


# ============================================================================
# Knowledge Base Storage
# ============================================================================

def load_knowledge_base() -> dict:
    """Load the knowledge base."""
    if not KNOWLEDGE_BASE_FILE.exists():
        return {
            'articles': [],      # Selected news articles
            'facts': [],         # Key facts/data points (legacy)
            'topics': {},        # Topic summaries
            'metadata': {
                'created': datetime.now().isoformat(),
                'last_updated': None,
                'total_articles': 0,
                'total_facts': 0
            }
        }
    try:
        with open(KNOWLEDGE_BASE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {
            'articles': [],
            'facts': [],
            'topics': {},
            'metadata': {'created': datetime.now().isoformat()}
        }


def save_knowledge_base(kb: dict):
    """Save the knowledge base."""
    DATA_DIR.mkdir(exist_ok=True)
    kb['metadata']['last_updated'] = datetime.now().isoformat()
    kb['metadata']['total_articles'] = len(kb.get('articles', []))
    with open(KNOWLEDGE_BASE_FILE, 'w', encoding='utf-8') as f:
        json.dump(kb, f, indent=2, ensure_ascii=False, default=str)


def load_facts_db() -> dict:
    """Load the structured facts database."""
    if not FACTS_FILE.exists():
        return {
            'facts': [],  # List of extracted facts
            'metadata': {
                'created': datetime.now().isoformat(),
                'last_updated': None,
                'total_facts': 0
            }
        }
    try:
        with open(FACTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {'facts': [], 'metadata': {}}


def save_facts_db(facts_db: dict):
    """Save the structured facts database."""
    DATA_DIR.mkdir(exist_ok=True)
    facts_db['metadata']['last_updated'] = datetime.now().isoformat()
    facts_db['metadata']['total_facts'] = len(facts_db.get('facts', []))
    with open(FACTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(facts_db, f, indent=2, ensure_ascii=False, default=str)


# ============================================================================
# Structured Fact Extraction (NEW)
# ============================================================================

def extract_facts_from_content(
    content: str,
    title: str,
    url: str,
    source: str,
    published: str = ""
) -> List[Dict]:
    """
    Use AI to extract structured facts from article content.
    
    Returns a list of fact dictionaries with:
    - fact_type: 'statistic', 'quote', 'claim', 'announcement', 'date'
    - text: The actual fact/quote
    - context: Brief context about the fact
    - citation: Ready-to-use markdown citation
    - keywords: List of topic keywords for matching
    - confidence: How confident we are this is accurate (high/medium/low)
    """
    if not OPENAI_AVAILABLE or not openai_client or not content:
        return []
    
    # Truncate content if too long
    content_for_extraction = content[:8000]
    
    prompt = f"""Analyze this article and extract SPECIFIC, CITABLE facts.

ARTICLE TITLE: {title}
SOURCE: {source}
PUBLISHED: {published or 'Unknown date'}
URL: {url}

CONTENT:
{content_for_extraction}

---

Extract facts in these categories:

1. STATISTICS - Numbers, percentages, measurements (e.g., "45% of newsrooms use AI")
2. QUOTES - Direct quotes from named people (e.g., Sam Altman said "...")
3. ANNOUNCEMENTS - Product launches, partnerships, policy changes
4. CLAIMS - Significant claims or findings from research
5. DATES - Important dates for events, launches, deadlines

For EACH fact, provide:
- The exact text/quote
- 2-3 keywords for topic matching
- Whether it's a hard fact (statistic/quote) or interpretation (claim)

Return as JSON array:
[
    {{
        "fact_type": "statistic|quote|announcement|claim|date",
        "text": "The exact fact or quote",
        "speaker": "Name if it's a quote, or null",
        "context": "One sentence of context",
        "keywords": ["keyword1", "keyword2", "keyword3"],
        "confidence": "high|medium|low"
    }}
]

ONLY extract facts that are:
- Specific and citable (not vague claims)
- From this article (not general knowledge)
- Useful for a journalist/newsletter writer

If the article has no extractable facts, return: []

Return ONLY valid JSON, no other text."""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",  # Fast and cheap for extraction
            messages=[
                {"role": "system", "content": "You are a research assistant extracting citable facts from articles. Be precise and only extract verifiable information."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,  # Low temperature for accuracy
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Handle both array and object responses
        if isinstance(result, dict):
            facts_list = result.get('facts', result.get('extracted_facts', []))
            if not facts_list and not any(k in result for k in ['facts', 'extracted_facts']):
                # The response might be the fact itself
                facts_list = [result] if 'text' in result else []
        else:
            facts_list = result if isinstance(result, list) else []
        
        # Enrich each fact with source information
        enriched_facts = []
        for fact in facts_list:
            if not isinstance(fact, dict) or not fact.get('text'):
                continue
                
            enriched_fact = {
                'id': hashlib.md5(f"{url}:{fact.get('text', '')[:50]}".encode()).hexdigest()[:12],
                'fact_type': fact.get('fact_type', 'claim'),
                'text': fact.get('text', ''),
                'speaker': fact.get('speaker'),
                'context': fact.get('context', ''),
                'keywords': fact.get('keywords', []),
                'confidence': fact.get('confidence', 'medium'),
                # Source information
                'source_title': title,
                'source_url': url,
                'source_name': source,
                'source_date': published,
                # Ready-to-use citation
                'citation': f"[{source}]({url})",
                'citation_full': f"According to [{title[:50]}...]({url})" if len(title) > 50 else f"According to [{title}]({url})",
                # Metadata
                'extracted_at': datetime.now().isoformat(),
                'used_count': 0
            }
            enriched_facts.append(enriched_fact)
        
        return enriched_facts
        
    except Exception as e:
        print(f"Fact extraction error: {e}")
        return []


def add_facts_to_db(facts: List[Dict]) -> int:
    """Add extracted facts to the facts database. Returns count added."""
    if not facts:
        return 0
    
    facts_db = load_facts_db()
    existing_ids = {f['id'] for f in facts_db['facts']}
    
    added = 0
    for fact in facts:
        if fact.get('id') and fact['id'] not in existing_ids:
            facts_db['facts'].append(fact)
            existing_ids.add(fact['id'])
            added += 1
    
    if added > 0:
        save_facts_db(facts_db)
    
    return added


def get_all_facts(
    fact_type: str = None,
    min_confidence: str = None,
    limit: int = None
) -> List[Dict]:
    """Get facts from the database with optional filtering."""
    facts_db = load_facts_db()
    facts = facts_db.get('facts', [])
    
    # Filter by type
    if fact_type:
        facts = [f for f in facts if f.get('fact_type') == fact_type]
    
    # Filter by confidence
    if min_confidence:
        confidence_order = {'high': 3, 'medium': 2, 'low': 1}
        min_level = confidence_order.get(min_confidence, 0)
        facts = [f for f in facts if confidence_order.get(f.get('confidence', 'low'), 0) >= min_level]
    
    # Sort by extraction date (newest first)
    facts.sort(key=lambda x: x.get('extracted_at', ''), reverse=True)
    
    if limit:
        facts = facts[:limit]
    
    return facts


# ============================================================================
# Article Management
# ============================================================================

def generate_article_id(url: str) -> str:
    """Generate a unique ID for an article based on URL."""
    return hashlib.md5(url.encode()).hexdigest()[:12]


# ============================================================================
# URL Validation
# ============================================================================

# Known fake/placeholder URL patterns to reject
FAKE_URL_PATTERNS = [
    'example.com', 'example.org', 'example.net',
    'placeholder', 'dummy', 'fake', 'test.com',
    'sample.com', 'lorem', 'xyz.com', 'foo.com',
    'bar.com', 'yoursite.com', 'website.com',
    'domain.com', 'url.com', 'link.com'
]


def is_url_fake(url: str) -> bool:
    """
    Check if a URL appears to be a placeholder/fake URL.
    
    IMPORTANT:
    - An EMPTY or MISSING URL is **not** treated as fake. Those articles stay.
    - Only obvious placeholder patterns (example.com, placeholder, dummy, etc.)
      count as fake.
    """
    if not url:
        # No URL provided: keep the article, don't treat as fake.
        return False
    url_lower = url.lower()
    return any(fake in url_lower for fake in FAKE_URL_PATTERNS)


def validate_url(url: str, timeout: int = 10) -> dict:
    """
    Validate a URL by checking if it's accessible.
    
    Returns:
        dict with:
        - valid: bool - whether URL is accessible
        - status_code: int or None
        - error: str or None
        - is_fake: bool - whether URL appears to be a placeholder
    """
    result = {
        'valid': False,
        'status_code': None,
        'error': None,
        'is_fake': False,
        'url': url
    }
    
    # Check for fake URLs first
    if is_url_fake(url):
        result['is_fake'] = True
        result['error'] = 'URL appears to be a placeholder/fake URL'
        return result
    
    # Check URL format
    if not url or not url.startswith(('http://', 'https://')):
        result['error'] = 'Invalid URL format (must start with http:// or https://)'
        return result
    
    try:
        # Make a HEAD request first (faster)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.head(url, timeout=timeout, allow_redirects=True, headers=headers)
        
        # Some sites don't allow HEAD, try GET
        if response.status_code >= 400:
            response = requests.get(url, timeout=timeout, allow_redirects=True, headers=headers)
        
        result['status_code'] = response.status_code
        result['valid'] = response.status_code < 400
        
        if not result['valid']:
            result['error'] = f'HTTP {response.status_code}'
            
    except requests.exceptions.Timeout:
        result['error'] = 'Request timed out'
    except requests.exceptions.ConnectionError:
        result['error'] = 'Connection failed'
    except requests.exceptions.TooManyRedirects:
        result['error'] = 'Too many redirects'
    except Exception as e:
        result['error'] = str(e)[:100]
    
    return result


def validate_all_articles(update_status: bool = True) -> dict:
    """
    Validate all URLs in the knowledge base.
    
    Args:
        update_status: If True, update each article's validation status
    
    Returns:
        dict with validation summary and list of invalid articles
    """
    kb = load_knowledge_base()
    articles = kb.get('articles', [])
    
    results = {
        'total': len(articles),
        'valid': 0,
        'invalid': 0,
        'fake': 0,
        'invalid_articles': [],
        'fake_articles': []
    }
    
    for article in articles:
        url = article.get('url', '')
        validation = validate_url(url)
        
        if validation['is_fake']:
            results['fake'] += 1
            results['fake_articles'].append({
                'id': article.get('id'),
                'title': article.get('title'),
                'url': url,
                'error': validation['error']
            })
        elif validation['valid']:
            results['valid'] += 1
        else:
            results['invalid'] += 1
            results['invalid_articles'].append({
                'id': article.get('id'),
                'title': article.get('title'),
                'url': url,
                'error': validation['error']
            })
        
        # Update article with validation status
        if update_status:
            article['url_validated'] = validation['valid']
            article['url_validation_date'] = datetime.now().isoformat()
            article['url_validation_error'] = validation['error']
            article['is_fake_url'] = validation['is_fake']
    
    if update_status:
        save_knowledge_base(kb)
    
    return results


def remove_fake_articles() -> int:
    """Remove all articles with fake/placeholder URLs. Returns count removed."""
    kb = load_knowledge_base()
    original_count = len(kb.get('articles', []))
    
    kb['articles'] = [
        a for a in kb.get('articles', [])
        if not is_url_fake(a.get('url', ''))
    ]
    
    removed = original_count - len(kb['articles'])
    if removed > 0:
        save_knowledge_base(kb)
    
    return removed


# ============================================================================
# Article Usage Tracking
# ============================================================================

def record_article_usage(
    article_id: str,
    newsletter_headline: str = "",
    newsletter_id: str = "",
    usage_type: str = "outline"
) -> bool:
    """
    Record that an article was used in a newsletter.
    
    Args:
        article_id: The article's ID
        newsletter_headline: The headline of the newsletter using it
        newsletter_id: Optional ID of the newsletter
        usage_type: 'outline', 'generation', 'citation'
    
    Returns:
        True if recorded successfully
    """
    kb = load_knowledge_base()
    
    for article in kb.get('articles', []):
        if article.get('id') == article_id:
            # Initialize usage tracking if not present
            if 'usage_history' not in article:
                article['usage_history'] = []
            
            # Record the usage
            article['usage_history'].append({
                'date': datetime.now().isoformat(),
                'newsletter_headline': newsletter_headline,
                'newsletter_id': newsletter_id,
                'usage_type': usage_type
            })
            
            # Increment usage count
            article['used_count'] = article.get('used_count', 0) + 1
            article['last_used'] = datetime.now().isoformat()
            
            save_knowledge_base(kb)
            return True
    
    return False


def record_article_usage_by_url(
    url: str,
    newsletter_headline: str = "",
    newsletter_id: str = "",
    usage_type: str = "outline"
) -> bool:
    """Record article usage by URL instead of ID."""
    article_id = generate_article_id(url)
    return record_article_usage(article_id, newsletter_headline, newsletter_id, usage_type)


def get_article_usage(article_id: str) -> dict:
    """Get usage history for an article."""
    kb = load_knowledge_base()
    
    for article in kb.get('articles', []):
        if article.get('id') == article_id:
            return {
                'title': article.get('title'),
                'url': article.get('url'),
                'used_count': article.get('used_count', 0),
                'last_used': article.get('last_used'),
                'usage_history': article.get('usage_history', [])
            }
    
    return {'error': 'Article not found'}


def get_most_used_articles(limit: int = 10) -> List[dict]:
    """Get the most frequently used articles."""
    kb = load_knowledge_base()
    articles = kb.get('articles', [])
    
    # Sort by usage count
    sorted_articles = sorted(
        articles,
        key=lambda x: x.get('used_count', 0),
        reverse=True
    )
    
    return sorted_articles[:limit]


def add_article(
    title: str,
    url: str,
    source: str,
    summary: str = "",
    published: str = "",
    category: str = "general",
    key_points: List[str] = None,
    validate: bool = True,
    skip_fake: bool = True
) -> dict:
    """
    Add a news article to the knowledge base.
    
    Args:
        title: Article headline
        url: Source URL (must be valid)
        source: Publication name
        summary: Brief summary
        published: Publication date
        category: Category (ai, africa, tech, policy, etc.)
        key_points: List of key facts from the article
        validate: Whether to validate the URL is accessible
        skip_fake: Whether to reject fake/placeholder URLs
    
    Returns the added article dict, or error dict if validation fails.
    """
    # CRITICAL: Check for fake URLs first
    if skip_fake and is_url_fake(url):
        return {
            'error': f'Rejected fake/placeholder URL: {url}',
            'is_fake': True
        }
    
    kb = load_knowledge_base()
    
    article_id = generate_article_id(url)
    
    # Check if already exists
    existing = next((a for a in kb['articles'] if a['id'] == article_id), None)
    if existing:
        return existing
    
    # Validate URL if requested (but don't block on timeout)
    url_valid = None
    validation_error = None
    if validate:
        try:
            validation = validate_url(url, timeout=5)
            url_valid = validation['valid']
            validation_error = validation['error']
        except:
            url_valid = None  # Unknown
    
    article = {
        'id': article_id,
        'title': title,
        'url': url,
        'source': source,
        'summary': summary,
        'published': published,
        'category': category,
        'key_points': key_points or [],
        'added_at': datetime.now().isoformat(),
        'used_count': 0,
        'usage_history': [],
        'url_validated': url_valid,
        'url_validation_date': datetime.now().isoformat() if validate else None,
        'url_validation_error': validation_error
    }
    
    kb['articles'].append(article)
    save_knowledge_base(kb)
    
    return article


def add_articles_batch(articles: List[dict]) -> int:
    """Add multiple articles at once. Returns count added."""
    kb = load_knowledge_base()
    added = 0
    
    existing_ids = {a['id'] for a in kb['articles']}
    
    for article in articles:
        url = article.get('url', article.get('link', ''))
        if not url:
            continue
            
        article_id = generate_article_id(url)
        if article_id in existing_ids:
            continue
        
        kb['articles'].append({
            'id': article_id,
            'title': article.get('title', 'Untitled'),
            'url': url,
            'source': article.get('source', 'Unknown'),
            'summary': article.get('summary', article.get('description', ''))[:500],
            'published': article.get('published', article.get('date', '')),
            'category': article.get('category', 'general'),
            'key_points': article.get('key_points', []),
            'added_at': datetime.now().isoformat(),
            'used_count': 0
        })
        existing_ids.add(article_id)
        added += 1
    
    save_knowledge_base(kb)
    return added


def remove_article(article_id: str) -> bool:
    """Remove an article from the knowledge base."""
    kb = load_knowledge_base()
    original_count = len(kb['articles'])
    kb['articles'] = [a for a in kb['articles'] if a['id'] != article_id]
    
    if len(kb['articles']) < original_count:
        save_knowledge_base(kb)
        return True
    return False


def get_articles(
    category: str = None,
    days: int = None,
    limit: int = None
) -> List[dict]:
    """
    Get articles from the knowledge base.
    
    Args:
        category: Filter by category
        days: Only articles from last N days
        limit: Maximum number to return
    """
    kb = load_knowledge_base()
    articles = kb.get('articles', [])
    
    # Filter by category
    if category:
        articles = [a for a in articles if a.get('category') == category]
    
    # Filter by date
    if days:
        cutoff = datetime.now() - timedelta(days=days)
        filtered = []
        for a in articles:
            added = a.get('added_at', '')
            if added:
                try:
                    added_dt = datetime.fromisoformat(added.replace('Z', '+00:00'))
                    if added_dt.replace(tzinfo=None) >= cutoff:
                        filtered.append(a)
                except:
                    filtered.append(a)  # Include if can't parse
        articles = filtered
    
    # Sort by added date (newest first)
    articles.sort(key=lambda x: x.get('added_at', ''), reverse=True)
    
    # Limit
    if limit:
        articles = articles[:limit]
    
    return articles


def clear_old_articles(days: int = 30) -> int:
    """Remove articles older than N days. Returns count removed."""
    kb = load_knowledge_base()
    cutoff = datetime.now() - timedelta(days=days)
    
    original_count = len(kb['articles'])
    
    kept = []
    for a in kb['articles']:
        added = a.get('added_at', '')
        if added:
            try:
                added_dt = datetime.fromisoformat(added.replace('Z', '+00:00'))
                if added_dt.replace(tzinfo=None) >= cutoff:
                    kept.append(a)
            except:
                kept.append(a)
    
    kb['articles'] = kept
    save_knowledge_base(kb)
    
    return original_count - len(kept)


# ============================================================================
# Semantic Relevance Matching (NEW)
# ============================================================================

def calculate_relevance_score(
    fact_or_article: Dict,
    topic: str,
    topic_keywords: List[str] = None
) -> float:
    """
    Calculate how relevant a fact or article is to a given topic.
    
    Uses keyword matching with weighted scoring:
    - Exact phrase match: +10 points
    - Keyword in title/text: +3 points
    - Keyword in keywords field: +5 points
    - Recent source: +2 points
    """
    if not topic:
        return 0.0
    
    topic_lower = topic.lower()
    topic_words = set(topic_lower.split())
    
    # Add any provided keywords
    if topic_keywords:
        topic_words.update(kw.lower() for kw in topic_keywords)
    
    # Remove common words
    stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 
                  'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                  'would', 'could', 'should', 'may', 'might', 'must', 'can',
                  'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
                  'as', 'into', 'through', 'during', 'before', 'after', 'and',
                  'or', 'but', 'if', 'then', 'because', 'while', 'although',
                  'this', 'that', 'these', 'those', 'it', 'its', 'how', 'what',
                  'why', 'when', 'where', 'who', 'which', 'about', 'your'}
    topic_words = topic_words - stop_words
    
    score = 0.0
    
    # Get searchable text from the item
    if 'text' in fact_or_article:
        # It's a fact
        searchable = (
            fact_or_article.get('text', '').lower() + ' ' +
            fact_or_article.get('context', '').lower() + ' ' +
            fact_or_article.get('source_title', '').lower()
        )
        item_keywords = [kw.lower() for kw in fact_or_article.get('keywords', [])]
    else:
        # It's an article
        searchable = (
            fact_or_article.get('title', '').lower() + ' ' +
            fact_or_article.get('summary', '').lower() + ' ' +
            ' '.join(fact_or_article.get('key_points', []))
        ).lower()
        item_keywords = []
    
    # Exact phrase match (highest value)
    if topic_lower in searchable:
        score += 10
    
    # Keyword matches
    for word in topic_words:
        if len(word) < 3:  # Skip very short words
            continue
        if word in searchable:
            score += 3
        if word in item_keywords:
            score += 5  # Higher score for matching extracted keywords
    
    # Recency bonus (if source date is recent)
    source_date = fact_or_article.get('source_date') or fact_or_article.get('published', '')
    if source_date:
        try:
            date_str = source_date[:10]
            source_dt = datetime.strptime(date_str, '%Y-%m-%d')
            days_old = (datetime.now() - source_dt).days
            if days_old <= 7:
                score += 3  # Very recent
            elif days_old <= 30:
                score += 1  # Recent
        except:
            pass
    
    # Confidence bonus for facts
    if fact_or_article.get('confidence') == 'high':
        score += 2
    
    return score


def get_relevant_facts(
    topic: str,
    max_facts: int = 15,
    min_relevance: float = 3.0,
    fact_types: List[str] = None
) -> List[Dict]:
    """
    Get facts that are relevant to a given topic, sorted by relevance.
    
    Args:
        topic: The newsletter topic/idea
        max_facts: Maximum number of facts to return
        min_relevance: Minimum relevance score to include
        fact_types: Optional list of fact types to include
    
    Returns list of relevant facts with relevance scores.
    """
    all_facts = get_all_facts()
    
    if not all_facts or not topic:
        return []
    
    # Filter by type if specified
    if fact_types:
        all_facts = [f for f in all_facts if f.get('fact_type') in fact_types]
    
    # Score each fact
    scored_facts = []
    for fact in all_facts:
        score = calculate_relevance_score(fact, topic)
        if score >= min_relevance:
            fact_with_score = fact.copy()
            fact_with_score['relevance_score'] = score
            scored_facts.append(fact_with_score)
    
    # Sort by relevance (highest first)
    scored_facts.sort(key=lambda x: x['relevance_score'], reverse=True)
    
    return scored_facts[:max_facts]


# ============================================================================
# Knowledge Retrieval for Generation (ENHANCED)
# ============================================================================

def get_knowledge_context(
    topic: str = "",
    max_articles: int = 10,
    max_chars: int = 4000
) -> str:
    """
    Build a context string from the knowledge base for use in generation.
    
    This provides FACTUAL CONTEXT only - it does NOT affect writing style.
    The fine-tuned model handles style; this provides the WHAT to write about.
    
    Args:
        topic: Optional topic to filter/prioritize
        max_articles: Maximum articles to include
        max_chars: Maximum character length
    
    Returns a formatted string of relevant knowledge.
    """
    articles = get_articles(limit=max_articles * 2)  # Get more, then filter
    
    if not articles:
        return ""
    
    # If topic provided, prioritize relevant articles
    if topic:
        # Score articles by relevance
        scored_articles = []
        for article in articles:
            score = calculate_relevance_score(article, topic)
            article_with_score = article.copy()
            article_with_score['_relevance'] = score
            scored_articles.append(article_with_score)
        
        # Sort by relevance
        scored_articles.sort(key=lambda x: x['_relevance'], reverse=True)
        articles = scored_articles
    
    # Build context
    context = "## KNOWLEDGE BASE - Recent AI News (for factual context)\n\n"
    context += "*These are verified sources - use them for facts and citations.*\n\n"
    
    char_count = len(context)
    articles_added = 0
    
    for article in articles:
        if articles_added >= max_articles:
            break
        
        # Skip articles with zero relevance if we have a topic
        if topic and article.get('_relevance', 0) == 0:
            continue
        
        entry = f"### {article.get('title', 'Untitled')}\n"
        entry += f"**Source:** {article.get('source', 'Unknown')} | "
        entry += f"**URL:** {article.get('url', 'N/A')}\n"
        
        if article.get('published'):
            entry += f"**Date:** {article['published']}\n"
        
        if article.get('summary'):
            entry += f"{article['summary'][:300]}...\n"
        
        if article.get('key_points'):
            entry += "**Key points:** " + ", ".join(article['key_points'][:3]) + "\n"
        
        entry += "\n---\n\n"
        
        if char_count + len(entry) > max_chars:
            break
        
        context += entry
        char_count += len(entry)
        articles_added += 1
    
    if articles_added == 0:
        return ""
    
    context += f"\n*{articles_added} articles from knowledge base.*\n"
    
    return context


def get_relevant_facts_context(
    topic: str,
    max_facts: int = 10,
    max_chars: int = 3000
) -> Tuple[str, List[Dict]]:
    """
    Get a formatted context string of relevant facts for generation.
    
    Returns:
        Tuple of (formatted_context_string, list_of_facts_used)
    
    This is the main function for automatic fact injection.
    """
    relevant_facts = get_relevant_facts(topic, max_facts=max_facts)
    
    if not relevant_facts:
        return "", []
    
    # Build context grouped by fact type
    context = """
## 📊 CITABLE FACTS FROM YOUR KNOWLEDGE BASE

These facts have been automatically matched to your topic. 
Each one includes a ready-to-use citation link.

### HOW TO USE THESE FACTS:
- Weave them naturally into your writing
- Include the [Source](url) link when citing
- Prioritize "high confidence" facts
- Facts are sorted by relevance to your topic

---

"""
    
    # Group by type
    facts_by_type = {}
    for fact in relevant_facts:
        ftype = fact.get('fact_type', 'other')
        if ftype not in facts_by_type:
            facts_by_type[ftype] = []
        facts_by_type[ftype].append(fact)
    
    type_labels = {
        'statistic': '📈 STATISTICS',
        'quote': '💬 QUOTES',
        'announcement': '📢 ANNOUNCEMENTS',
        'claim': '🔍 KEY CLAIMS',
        'date': '📅 IMPORTANT DATES'
    }
    
    char_count = len(context)
    facts_used = []
    
    for ftype, type_facts in facts_by_type.items():
        if char_count >= max_chars:
            break
            
        type_header = f"\n### {type_labels.get(ftype, ftype.upper())}\n\n"
        if char_count + len(type_header) > max_chars:
            break
        context += type_header
        char_count += len(type_header)
        
        for fact in type_facts[:5]:  # Max 5 per type
            if char_count >= max_chars:
                break
            
            confidence_emoji = {'high': '🟢', 'medium': '🟡', 'low': '🟠'}.get(
                fact.get('confidence', 'medium'), '🟡'
            )
            
            entry = f"- {confidence_emoji} **{fact['text'][:200]}**"
            if fact.get('speaker'):
                entry += f" — *{fact['speaker']}*"
            entry += f"\n  - 📎 Citation: {fact.get('citation', 'No URL')}"
            entry += f" | Date: {fact.get('source_date', 'Unknown')[:10] if fact.get('source_date') else 'Unknown'}"
            entry += f"\n  - Relevance: {fact.get('relevance_score', 0):.1f}\n\n"
            
            if char_count + len(entry) > max_chars:
                break
            
            context += entry
            char_count += len(entry)
            facts_used.append(fact)
    
    context += f"\n---\n*{len(facts_used)} relevant facts automatically matched to your topic.*\n"
    
    return context, facts_used


def mark_facts_as_used(fact_ids: List[str]):
    """Mark facts as used in a newsletter (for tracking)."""
    if not fact_ids:
        return
    
    facts_db = load_facts_db()
    for fact in facts_db['facts']:
        if fact.get('id') in fact_ids:
            fact['used_count'] = fact.get('used_count', 0) + 1
            fact['last_used'] = datetime.now().isoformat()
    
    save_facts_db(facts_db)


def get_stats() -> dict:
    """Get knowledge base statistics."""
    kb = load_knowledge_base()
    articles = kb.get('articles', [])
    
    # Count by category
    by_category = {}
    for a in articles:
        cat = a.get('category', 'general')
        by_category[cat] = by_category.get(cat, 0) + 1
    
    # Count by source
    by_source = {}
    for a in articles:
        source = a.get('source', 'Unknown')
        by_source[source] = by_source.get(source, 0) + 1
    
    # Recent articles (last 2 days)
    cutoff = datetime.now() - timedelta(days=2)
    recent = 0
    for a in articles:
        added = a.get('added_at', '')
        if added:
            try:
                added_dt = datetime.fromisoformat(added.replace('Z', '+00:00'))
                if added_dt.replace(tzinfo=None) >= cutoff:
                    recent += 1
            except:
                pass
    
    return {
        'total_articles': len(articles),
        'recent_articles': recent,
        'by_category': by_category,
        'by_source': by_source,
        'last_updated': kb.get('metadata', {}).get('last_updated')
    }


# ============================================================================
# Search
# ============================================================================

def search_articles(query: str, limit: int = 10) -> List[dict]:
    """Search articles by keyword."""
    articles = get_articles()
    query_lower = query.lower()
    query_words = set(query_lower.split())
    
    results = []
    for article in articles:
        title = article.get('title', '').lower()
        summary = article.get('summary', '').lower()
        text = title + ' ' + summary
        
        # Check for matches
        if query_lower in text or any(word in text for word in query_words):
            results.append(article)
    
    return results[:limit]


# ============================================================================
# URL Content Extraction
# ============================================================================

def extract_article_from_url(url: str, timeout: int = 15) -> dict:
    """
    Fetch and extract article content from a URL.
    
    Returns a dict with title, content, summary, published date, etc.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title
        title = ""
        if soup.find('h1'):
            title = soup.find('h1').get_text(strip=True)
        elif soup.find('title'):
            title = soup.find('title').get_text(strip=True)
        elif soup.find('meta', {'property': 'og:title'}):
            title = soup.find('meta', {'property': 'og:title'}).get('content', '')
        
        # Extract source/site name
        source = ""
        if soup.find('meta', {'property': 'og:site_name'}):
            source = soup.find('meta', {'property': 'og:site_name'}).get('content', '')
        else:
            # Extract from URL domain
            from urllib.parse import urlparse
            parsed = urlparse(url)
            source = parsed.netloc.replace('www.', '')
        
        # Extract published date
        published = ""
        date_meta = soup.find('meta', {'property': 'article:published_time'})
        if date_meta:
            published = date_meta.get('content', '')[:10]
        else:
            time_tag = soup.find('time')
            if time_tag and time_tag.get('datetime'):
                published = time_tag.get('datetime')[:10]
        
        # Extract description/summary
        summary = ""
        if soup.find('meta', {'name': 'description'}):
            summary = soup.find('meta', {'name': 'description'}).get('content', '')
        elif soup.find('meta', {'property': 'og:description'}):
            summary = soup.find('meta', {'property': 'og:description'}).get('content', '')
        
        # Extract main content
        content = ""
        article_tag = soup.find('article')
        if article_tag:
            # Get all paragraphs in article
            paragraphs = article_tag.find_all('p')
            content = "\n\n".join([p.get_text(strip=True) for p in paragraphs[:20]])
        else:
            # Fallback: get main text
            for tag in soup.find_all(['script', 'style', 'nav', 'header', 'footer']):
                tag.decompose()
            paragraphs = soup.find_all('p')
            content = "\n\n".join([p.get_text(strip=True) for p in paragraphs[:15]])
        
        # Extract key points (first few sentences)
        key_points = []
        if content:
            sentences = re.split(r'[.!?]+', content)
            key_points = [s.strip() for s in sentences[:5] if len(s.strip()) > 30]
        
        # If no summary, use first part of content
        if not summary and content:
            summary = content[:300] + "..." if len(content) > 300 else content
        
        return {
            'success': True,
            'title': title or "Untitled Article",
            'url': url,
            'source': source or "Unknown",
            'summary': summary[:500],
            'published': published or datetime.now().strftime('%Y-%m-%d'),
            'content': content[:5000],
            'key_points': key_points[:5],
            'category': 'article',
            'type': 'url'
        }
        
    except requests.exceptions.Timeout:
        return {'success': False, 'error': 'Request timed out'}
    except requests.exceptions.RequestException as e:
        return {'success': False, 'error': f'Failed to fetch URL: {str(e)}'}
    except Exception as e:
        return {'success': False, 'error': f'Error parsing content: {str(e)}'}


def add_from_url(url: str, extract_facts: bool = True) -> dict:
    """
    Add an article to the knowledge base by fetching its content from a URL.
    
    NEW: Optionally extracts structured facts for automatic injection.
    
    Args:
        url: The article URL
        extract_facts: Whether to extract structured facts (default True)
    
    Returns the added article or error dict.
    """
    # First extract the content
    extracted = extract_article_from_url(url)
    
    if not extracted.get('success'):
        return extracted
    
    # Add to knowledge base
    article = add_article(
        title=extracted['title'],
        url=extracted['url'],
        source=extracted['source'],
        summary=extracted['summary'],
        published=extracted['published'],
        category=extracted.get('category', 'article'),
        key_points=extracted.get('key_points', [])
    )
    
    # Store full content separately if needed
    facts_extracted = 0
    if extracted.get('content'):
        # Add content to the article
        kb = load_knowledge_base()
        for a in kb['articles']:
            if a['id'] == article['id']:
                a['full_content'] = extracted['content'][:5000]
                a['type'] = 'url'
                break
        save_knowledge_base(kb)
        
        # NEW: Extract structured facts from the content
        if extract_facts and OPENAI_AVAILABLE:
            facts = extract_facts_from_content(
                content=extracted['content'],
                title=extracted['title'],
                url=url,
                source=extracted['source'],
                published=extracted['published']
            )
            if facts:
                facts_extracted = add_facts_to_db(facts)
    
    return {
        'success': True, 
        'article': article,
        'facts_extracted': facts_extracted
    }


# ============================================================================
# PDF Content Extraction
# ============================================================================

def extract_text_from_pdf(pdf_content: bytes) -> str:
    """
    Extract text from PDF bytes.
    
    Tries multiple methods in order of preference.
    """
    text = ""
    
    # Try PyPDF2/pypdf first
    try:
        from pypdf import PdfReader
        from io import BytesIO
        
        reader = PdfReader(BytesIO(pdf_content))
        for page in reader.pages[:30]:  # Limit to first 30 pages
            text += page.extract_text() + "\n\n"
        
        if text.strip():
            return text
    except ImportError:
        pass
    except Exception:
        pass
    
    # Try pdfplumber
    try:
        import pdfplumber
        from io import BytesIO
        
        with pdfplumber.open(BytesIO(pdf_content)) as pdf:
            for page in pdf.pages[:30]:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"
        
        if text.strip():
            return text
    except ImportError:
        pass
    except Exception:
        pass
    
    return text


def add_from_pdf(
    pdf_content: bytes,
    filename: str,
    title: str = "",
    source: str = "",
    category: str = "report",
    published: str = "",
    extract_facts: bool = True
) -> dict:
    """
    Add a PDF document to the knowledge base.
    
    NEW: Optionally extracts structured facts for automatic injection.
    
    Args:
        pdf_content: The raw PDF bytes
        filename: Original filename
        title: Optional title (will extract from PDF if not provided)
        source: Source/publisher name
        category: Category (report, research, whitepaper, etc.)
        published: Publication date
        extract_facts: Whether to extract structured facts (default True)
    
    Returns dict with success status and article.
    """
    # Extract text from PDF
    text = extract_text_from_pdf(pdf_content)
    
    if not text:
        return {
            'success': False, 
            'error': 'Could not extract text from PDF. Make sure pypdf or pdfplumber is installed.'
        }
    
    # Generate a unique ID based on content hash
    content_hash = hashlib.md5(pdf_content[:10000]).hexdigest()[:12]
    url = f"pdf://{content_hash}/{filename}"
    
    # Extract title from first line if not provided
    if not title:
        first_lines = text.split('\n')[:5]
        for line in first_lines:
            line = line.strip()
            if len(line) > 10 and len(line) < 200:
                title = line
                break
    
    if not title:
        title = filename.replace('.pdf', '').replace('_', ' ').replace('-', ' ').title()
    
    # Create summary from first 500 chars
    clean_text = re.sub(r'\s+', ' ', text)
    summary = clean_text[:500] + "..." if len(clean_text) > 500 else clean_text
    
    # Extract key points (sentences that look important)
    sentences = re.split(r'[.!?]+', clean_text)
    key_points = []
    keywords = ['key', 'important', 'main', 'finding', 'conclusion', 'result', 'significant']
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) > 50 and len(sentence) < 300:
            if any(kw in sentence.lower() for kw in keywords):
                key_points.append(sentence)
        if len(key_points) >= 5:
            break
    
    # If no key points found, just use first few meaningful sentences
    if not key_points:
        key_points = [s.strip() for s in sentences[:5] if len(s.strip()) > 50]
    
    # Add to knowledge base
    kb = load_knowledge_base()
    
    article_id = content_hash
    
    # Check if already exists
    existing = next((a for a in kb['articles'] if a['id'] == article_id), None)
    if existing:
        return {'success': True, 'article': existing, 'message': 'PDF already in knowledge base'}
    
    pub_date = published or datetime.now().strftime('%Y-%m-%d')
    source_name = source or "PDF Upload"
    
    article = {
        'id': article_id,
        'title': title,
        'url': url,
        'source': source_name,
        'summary': summary,
        'published': pub_date,
        'category': category,
        'key_points': key_points[:5],
        'added_at': datetime.now().isoformat(),
        'used_count': 0,
        'type': 'pdf',
        'filename': filename,
        'full_content': clean_text[:10000]  # Store first 10k chars
    }
    
    kb['articles'].append(article)
    save_knowledge_base(kb)
    
    # NEW: Extract structured facts from PDF content
    facts_extracted = 0
    if extract_facts and OPENAI_AVAILABLE:
        facts = extract_facts_from_content(
            content=clean_text[:8000],
            title=title,
            url=url,
            source=source_name,
            published=pub_date
        )
        if facts:
            facts_extracted = add_facts_to_db(facts)
    
    return {
        'success': True, 
        'article': article,
        'facts_extracted': facts_extracted
    }


# ============================================================================
# Metadata
# ============================================================================

def get_kb_metadata() -> dict:
    """Get detailed metadata about the knowledge base."""
    kb = load_knowledge_base()
    articles = kb.get('articles', [])
    
    # Count by type
    by_type = {}
    for a in articles:
        t = a.get('type', 'article')
        by_type[t] = by_type.get(t, 0) + 1
    
    # Get date range
    dates = []
    for a in articles:
        if a.get('published'):
            try:
                dates.append(a['published'][:10])
            except:
                pass
    
    oldest = min(dates) if dates else None
    newest = max(dates) if dates else None
    
    return {
        'total_articles': len(articles),
        'by_type': by_type,
        'date_range': {'oldest': oldest, 'newest': newest},
        'last_updated': kb.get('metadata', {}).get('last_updated'),
        'categories': list(set(a.get('category', 'general') for a in articles)),
        'sources': list(set(a.get('source', 'Unknown') for a in articles))
    }


def get_facts_stats() -> dict:
    """Get statistics about extracted facts."""
    facts_db = load_facts_db()
    facts = facts_db.get('facts', [])
    
    # Count by type
    by_type = {}
    for f in facts:
        ftype = f.get('fact_type', 'other')
        by_type[ftype] = by_type.get(ftype, 0) + 1
    
    # Count by confidence
    by_confidence = {}
    for f in facts:
        conf = f.get('confidence', 'unknown')
        by_confidence[conf] = by_confidence.get(conf, 0) + 1
    
    # Count used vs unused
    used = sum(1 for f in facts if f.get('used_count', 0) > 0)
    
    # Count by source
    by_source = {}
    for f in facts:
        source = f.get('source_name', 'Unknown')
        by_source[source] = by_source.get(source, 0) + 1
    
    return {
        'total_facts': len(facts),
        'by_type': by_type,
        'by_confidence': by_confidence,
        'used_facts': used,
        'unused_facts': len(facts) - used,
        'by_source': by_source,
        'last_updated': facts_db.get('metadata', {}).get('last_updated')
    }


def clear_old_facts(days: int = 60) -> int:
    """Remove facts older than N days. Returns count removed."""
    facts_db = load_facts_db()
    cutoff = datetime.now() - timedelta(days=days)
    
    original_count = len(facts_db['facts'])
    
    kept = []
    for f in facts_db['facts']:
        extracted = f.get('extracted_at', '')
        if extracted:
            try:
                extracted_dt = datetime.fromisoformat(extracted.replace('Z', '+00:00'))
                if extracted_dt.replace(tzinfo=None) >= cutoff:
                    kept.append(f)
            except:
                kept.append(f)
        else:
            kept.append(f)
    
    facts_db['facts'] = kept
    save_facts_db(facts_db)
    
    return original_count - len(kept)


# ============================================================================
# Batch Processing - Extract Facts from All Articles
# ============================================================================

def process_all_articles_for_facts(
    fetch_missing_content: bool = True,
    progress_callback = None
) -> Dict:
    """
    Process all articles in the Knowledge Base to extract structured facts.
    
    This function:
    1. Iterates through all articles
    2. Fetches full content for articles that don't have it (if enabled)
    3. Extracts structured facts from each article
    4. Saves everything back to the database
    
    Args:
        fetch_missing_content: Whether to fetch content for articles without it
        progress_callback: Optional function(message, progress) for UI updates
    
    Returns:
        Dict with statistics about the processing
    """
    import time
    
    kb = load_knowledge_base()
    articles = kb.get('articles', [])
    
    stats = {
        'total_articles': len(articles),
        'articles_processed': 0,
        'articles_skipped': 0,
        'content_fetched': 0,
        'facts_extracted': 0,
        'facts_added': 0,
        'errors': []
    }
    
    if not articles:
        return stats
    
    for i, article in enumerate(articles):
        title = article.get('title', 'Untitled')[:50]
        url = article.get('url', '')
        
        # Progress update
        progress = (i + 1) / len(articles)
        if progress_callback:
            progress_callback(f"Processing: {title}...", progress)
        
        # Skip PDFs for now (they should already have content)
        if url.startswith('pdf://'):
            content = article.get('full_content', '')
            if not content or len(content) < 100:
                stats['articles_skipped'] += 1
                continue
        else:
            # Check if we need to fetch content
            content = article.get('full_content', '')
            
            if (not content or len(content) < 500) and fetch_missing_content and url:
                try:
                    extracted = extract_article_from_url(url)
                    if extracted.get('success') and extracted.get('content'):
                        article['full_content'] = extracted['content'][:5000]
                        content = extracted['content']
                        stats['content_fetched'] += 1
                        # Rate limit to avoid being blocked
                        time.sleep(0.5)
                except Exception as e:
                    stats['errors'].append(f"{title}: {str(e)[:50]}")
                    content = article.get('summary', '')
        
        # Extract facts if we have content
        if content and len(content) > 100:
            try:
                facts = extract_facts_from_content(
                    content=content,
                    title=article.get('title', ''),
                    url=url,
                    source=article.get('source', 'Unknown'),
                    published=article.get('published', '')
                )
                
                if facts:
                    stats['facts_extracted'] += len(facts)
                    added = add_facts_to_db(facts)
                    stats['facts_added'] += added
                
                stats['articles_processed'] += 1
                
            except Exception as e:
                stats['errors'].append(f"{title}: {str(e)[:50]}")
        else:
            stats['articles_skipped'] += 1
    
    # Save updated KB with any new content
    if stats['content_fetched'] > 0:
        save_knowledge_base(kb)
    
    return stats


def get_articles_without_facts() -> List[Dict]:
    """Get articles that don't have facts extracted yet."""
    articles = get_articles(limit=500)
    facts_db = load_facts_db()
    
    # Get all source URLs that have facts
    urls_with_facts = set()
    for fact in facts_db.get('facts', []):
        url = fact.get('source_url', '')
        if url:
            urls_with_facts.add(url)
    
    # Find articles without facts
    articles_without = []
    for article in articles:
        url = article.get('url', '')
        if url and url not in urls_with_facts:
            articles_without.append(article)
    
    return articles_without

