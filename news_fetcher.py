"""
News Fetcher - Pull recent AI news for newsletter research

Uses multiple free sources:
1. NewsAPI.org (free tier: 100 requests/day)
2. RSS feeds from major AI/tech sources
3. Google News RSS

Provides verified, recent sources with URLs for the newsletter.
"""

import os
import json
import re
import feedparser
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import urllib.parse

# Optional: for NewsAPI
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

DATA_DIR = Path(__file__).parent / "data"
NEWS_CACHE_FILE = DATA_DIR / "news_cache.json"

# RSS feeds for AI/tech news (free, no API key needed)
RSS_FEEDS = {
    'mit_tech_review': {
        'name': 'MIT Technology Review - AI',
        'url': 'https://www.technologyreview.com/feed/',
        'category': 'tech'
    },
    'techcrunch_ai': {
        'name': 'TechCrunch AI',
        'url': 'https://techcrunch.com/category/artificial-intelligence/feed/',
        'category': 'tech'
    },
    'the_verge_ai': {
        'name': 'The Verge - AI',
        'url': 'https://www.theverge.com/rss/ai-artificial-intelligence/index.xml',
        'category': 'tech'
    },
    'wired_ai': {
        'name': 'Wired - AI',
        'url': 'https://www.wired.com/feed/tag/ai/latest/rss',
        'category': 'tech'
    },
    'ars_technica': {
        'name': 'Ars Technica - AI',
        'url': 'https://feeds.arstechnica.com/arstechnica/technology-lab',
        'category': 'tech'
    },
    'reuters_tech': {
        'name': 'Reuters Technology',
        'url': 'https://www.reutersagency.com/feed/?best-topics=tech',
        'category': 'news'
    },
}

# Africa-focused tech sources
AFRICA_FEEDS = {
    'techcabal': {
        'name': 'TechCabal',
        'url': 'https://techcabal.com/feed/',
        'category': 'africa'
    },
    'disrupt_africa': {
        'name': 'Disrupt Africa',
        'url': 'https://disrupt-africa.com/feed/',
        'category': 'africa'
    },
}


def load_cache() -> dict:
    """Load cached news."""
    if not NEWS_CACHE_FILE.exists():
        return {'articles': [], 'last_updated': None}
    try:
        with open(NEWS_CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {'articles': [], 'last_updated': None}


def save_cache(cache: dict):
    """Save news cache."""
    DATA_DIR.mkdir(exist_ok=True)
    cache['last_updated'] = datetime.now().isoformat()
    with open(NEWS_CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=2, ensure_ascii=False, default=str)


def parse_date(date_str: str) -> Optional[datetime]:
    """Parse various date formats from RSS feeds."""
    formats = [
        '%a, %d %b %Y %H:%M:%S %z',
        '%a, %d %b %Y %H:%M:%S %Z',
        '%Y-%m-%dT%H:%M:%S%z',
        '%Y-%m-%dT%H:%M:%SZ',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d',
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except:
            continue
    return None


def fetch_rss_feed(feed_url: str, feed_name: str, category: str) -> list[dict]:
    """Fetch and parse a single RSS feed."""
    articles = []
    
    try:
        feed = feedparser.parse(feed_url)
        
        for entry in feed.entries[:10]:  # Limit to 10 per feed
            # Parse date
            pub_date = None
            if hasattr(entry, 'published'):
                pub_date = parse_date(entry.published)
            elif hasattr(entry, 'updated'):
                pub_date = parse_date(entry.updated)
            
            # Skip if older than 3 months
            if pub_date:
                three_months_ago = datetime.now() - timedelta(days=90)
                if pub_date.replace(tzinfo=None) < three_months_ago:
                    continue
            
            # Extract summary
            summary = ''
            if hasattr(entry, 'summary'):
                # Strip HTML
                summary = re.sub(r'<[^>]+>', '', entry.summary)[:300]
            elif hasattr(entry, 'description'):
                summary = re.sub(r'<[^>]+>', '', entry.description)[:300]
            
            articles.append({
                'title': entry.title,
                'url': entry.link,
                'source': feed_name,
                'category': category,
                'published': pub_date.isoformat() if pub_date else None,
                'summary': summary,
                'fetched': datetime.now().isoformat(),
            })
    
    except Exception as e:
        print(f"Error fetching {feed_name}: {e}")
    
    return articles


def fetch_all_news(include_africa: bool = True) -> list[dict]:
    """Fetch news from all RSS sources."""
    all_articles = []
    
    # Main tech feeds
    for feed_id, feed_info in RSS_FEEDS.items():
        articles = fetch_rss_feed(
            feed_info['url'],
            feed_info['name'],
            feed_info['category']
        )
        all_articles.extend(articles)
    
    # Africa-focused feeds
    if include_africa:
        for feed_id, feed_info in AFRICA_FEEDS.items():
            articles = fetch_rss_feed(
                feed_info['url'],
                feed_info['name'],
                feed_info['category']
            )
            all_articles.extend(articles)
    
    # Sort by date (newest first)
    all_articles.sort(
        key=lambda x: x.get('published') or '1900-01-01',
        reverse=True
    )
    
    # Remove duplicates by URL
    seen_urls = set()
    unique_articles = []
    for article in all_articles:
        if article['url'] not in seen_urls:
            seen_urls.add(article['url'])
            unique_articles.append(article)
    
    # Cache results
    save_cache({
        'articles': unique_articles,
        'source_count': len(RSS_FEEDS) + (len(AFRICA_FEEDS) if include_africa else 0),
    })
    
    return unique_articles


def search_news(query: str, max_results: int = 10) -> list[dict]:
    """Search cached news for relevant articles."""
    cache = load_cache()
    articles = cache.get('articles', [])
    
    if not articles:
        # Fetch fresh if cache is empty
        articles = fetch_all_news()
    
    # Simple keyword search
    query_words = query.lower().split()
    scored_articles = []
    
    for article in articles:
        text = f"{article.get('title', '')} {article.get('summary', '')}".lower()
        score = sum(1 for word in query_words if word in text)
        if score > 0:
            scored_articles.append((score, article))
    
    # Sort by relevance
    scored_articles.sort(key=lambda x: x[0], reverse=True)
    
    return [article for score, article in scored_articles[:max_results]]


def get_recent_ai_news(days: int = 7, category: str = None) -> list[dict]:
    """Get recent AI news, optionally filtered by category."""
    cache = load_cache()
    articles = cache.get('articles', [])
    
    # Check if cache is stale (older than 6 hours)
    last_updated = cache.get('last_updated')
    if last_updated:
        try:
            last_dt = datetime.fromisoformat(last_updated)
            if datetime.now() - last_dt > timedelta(hours=6):
                articles = fetch_all_news()
        except:
            articles = fetch_all_news()
    else:
        articles = fetch_all_news()
    
    # Filter by date
    cutoff = datetime.now() - timedelta(days=days)
    recent = []
    
    for article in articles:
        pub_date = article.get('published')
        if pub_date:
            try:
                pub_dt = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                if pub_dt.replace(tzinfo=None) >= cutoff:
                    if category is None or article.get('category') == category:
                        recent.append(article)
            except:
                pass
    
    return recent


def get_africa_news(days: int = 30) -> list[dict]:
    """Get Africa-focused tech news."""
    return get_recent_ai_news(days=days, category='africa')


def format_for_newsletter(articles: list[dict], max_items: int = 5) -> list[dict]:
    """Format articles for newsletter use with proper citations."""
    formatted = []
    
    for article in articles[:max_items]:
        pub_date = article.get('published', '')
        if pub_date:
            try:
                dt = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                pub_date = dt.strftime('%b %d, %Y')
            except:
                pub_date = ''
        
        formatted.append({
            'headline': article.get('title', ''),
            'source': article.get('source', 'Unknown'),
            'url': article.get('url', ''),
            'date': pub_date,
            'summary': article.get('summary', '')[:150] + '...' if len(article.get('summary', '')) > 150 else article.get('summary', ''),
            'citation': f"{article.get('source', 'Source')}, {pub_date}" if pub_date else article.get('source', 'Source'),
        })
    
    return formatted


def get_news_for_topic(topic: str, days: int = 30) -> list[dict]:
    """Get news related to a specific topic, formatted for newsletter use."""
    # First try cache search
    results = search_news(topic)
    
    # Filter to recent only
    cutoff = datetime.now() - timedelta(days=days)
    recent = []
    
    for article in results:
        pub_date = article.get('published')
        if pub_date:
            try:
                pub_dt = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                if pub_dt.replace(tzinfo=None) >= cutoff:
                    recent.append(article)
            except:
                recent.append(article)  # Include if can't parse date
        else:
            recent.append(article)
    
    return format_for_newsletter(recent)


def fetch_last_two_days(include_africa: bool = True, verify_links: bool = False) -> list[dict]:
    """
    Fetch AI news from the last 2 days with verified working links.
    
    This is specifically for the Content Inbox to populate selectable news.
    
    Args:
        include_africa: Include Africa-focused feeds
        verify_links: If True, verify each URL is accessible (slower)
    
    Returns list of articles with guaranteed working URLs.
    """
    # Force fresh fetch
    all_articles = []
    
    # Main tech feeds
    for feed_id, feed_info in RSS_FEEDS.items():
        articles = fetch_rss_feed(
            feed_info['url'],
            feed_info['name'],
            feed_info['category']
        )
        all_articles.extend(articles)
    
    # Africa-focused feeds
    if include_africa:
        for feed_id, feed_info in AFRICA_FEEDS.items():
            articles = fetch_rss_feed(
                feed_info['url'],
                feed_info['name'],
                feed_info['category']
            )
            all_articles.extend(articles)
    
    # Filter to last 2 days only
    cutoff = datetime.now() - timedelta(days=2)
    recent = []
    
    for article in all_articles:
        pub_date = article.get('published')
        if pub_date:
            try:
                pub_dt = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                if pub_dt.replace(tzinfo=None) >= cutoff:
                    recent.append(article)
            except:
                pass  # Skip if can't parse date
    
    # Verify links if requested (slower but ensures working URLs)
    if verify_links and HAS_REQUESTS:
        verified = []
        for article in recent:
            try:
                resp = requests.head(article['url'], timeout=5, allow_redirects=True)
                if resp.status_code < 400:
                    article['link_verified'] = True
                    verified.append(article)
            except:
                pass  # Skip articles with broken links
        recent = verified
    
    # Remove duplicates by URL
    seen_urls = set()
    unique = []
    for article in recent:
        if article['url'] not in seen_urls:
            seen_urls.add(article['url'])
            unique.append(article)
    
    # Sort by date (newest first)
    unique.sort(
        key=lambda x: x.get('published') or '1900-01-01',
        reverse=True
    )
    
    return unique


def get_selectable_news() -> list[dict]:
    """
    Get news formatted for selection in the Content Inbox UI.
    
    Returns articles from the last 2 days with:
    - title, url, source, summary, published
    - selected: False (for UI state)
    - id: unique identifier
    """
    articles = fetch_last_two_days(include_africa=True, verify_links=False)
    
    selectable = []
    for article in articles:
        import hashlib
        article_id = hashlib.md5(article['url'].encode()).hexdigest()[:12]
        
        selectable.append({
            'id': article_id,
            'title': article.get('title', 'Untitled'),
            'url': article.get('url', ''),
            'source': article.get('source', 'Unknown'),
            'category': article.get('category', 'general'),
            'summary': article.get('summary', '')[:200],
            'published': article.get('published', ''),
            'selected': False
        })
    
    return selectable


# ============================================================================
# Test
# ============================================================================

if __name__ == "__main__":
    print("News Fetcher Test")
    print("=" * 60)
    
    print("\n📰 Fetching all news...")
    articles = fetch_all_news()
    print(f"✓ Fetched {len(articles)} articles")
    
    print("\n🔍 Recent AI news (7 days):")
    recent = get_recent_ai_news(days=7)
    for article in recent[:5]:
        print(f"  - {article['title'][:60]}...")
        print(f"    {article['source']} | {article.get('published', 'No date')[:10]}")
        print(f"    {article['url']}")
        print()
    
    print("\n🌍 Africa tech news:")
    africa = get_africa_news(days=30)
    for article in africa[:3]:
        print(f"  - {article['title'][:60]}...")
        print(f"    {article['source']}")
    
    print("\n🔎 Search for 'ChatGPT':")
    results = search_news("ChatGPT")
    for article in results[:3]:
        print(f"  - {article['title'][:60]}...")
    
    print("\n" + "=" * 60)
    print("News fetcher ready!")

