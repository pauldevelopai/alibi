"""
Substack Archive Scraper

Scrapes newsletter posts from a Substack archive page and saves them as JSONL.
Targets: https://developai.substack.com/archive
"""

import json
import time
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

import requests
from bs4 import BeautifulSoup


# Configuration
SUBSTACK_URL = "https://developai.substack.com"
ARCHIVE_URL = f"{SUBSTACK_URL}/archive"
DATA_DIR = Path(__file__).parent / "data"
OUTPUT_FILE = DATA_DIR / "newsletters_raw.jsonl"

# Request settings
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}
REQUEST_DELAY = 1.5  # seconds between requests to be polite


def fetch_page(url: str) -> Optional[str]:
    """Fetch a page and return its HTML content."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None


def parse_archive_page(html: str) -> list[dict]:
    """
    Parse the archive page to extract post links and metadata.
    Returns a list of dicts with: title, url, published_date, summary
    """
    soup = BeautifulSoup(html, "lxml")
    posts = []
    
    # Substack archive uses various structures. Try multiple selectors.
    # Common patterns: div with class containing 'post', article elements, etc.
    
    # Try finding post containers - Substack often uses these patterns
    post_containers = soup.select('div[class*="post-preview"]')
    
    if not post_containers:
        post_containers = soup.select('article')
    
    if not post_containers:
        # Fallback: look for links that point to /p/ (post URLs)
        post_containers = soup.select('a[href*="/p/"]')
    
    # If we found direct links, handle differently
    if post_containers and post_containers[0].name == 'a':
        seen_urls = set()
        for link in post_containers:
            url = link.get('href', '')
            if not url.startswith('http'):
                url = SUBSTACK_URL + url
            
            # Skip if we've seen this URL or it's not a post
            if url in seen_urls or '/p/' not in url:
                continue
            seen_urls.add(url)
            
            # Try to find the title
            title_elem = link.select_one('h2, h3, [class*="title"]')
            title = title_elem.get_text(strip=True) if title_elem else link.get_text(strip=True)
            
            if title and len(title) > 5:  # Skip very short/empty titles
                posts.append({
                    'title': title,
                    'url': url,
                    'published_date': None,
                    'summary': None
                })
    else:
        # Handle structured post containers
        for container in post_containers:
            post_data = extract_post_from_container(container)
            if post_data:
                posts.append(post_data)
    
    return posts


def extract_post_from_container(container) -> Optional[dict]:
    """Extract post data from a container element."""
    # Find the link to the post
    link = container.select_one('a[href*="/p/"]')
    if not link:
        link = container.find('a', href=True)
    
    if not link:
        return None
    
    url = link.get('href', '')
    if not url.startswith('http'):
        url = SUBSTACK_URL + url
    
    if '/p/' not in url:
        return None
    
    # Find title - try various selectors
    title_elem = container.select_one('h2, h3, [class*="title"], [class*="headline"]')
    if not title_elem:
        title_elem = link
    title = title_elem.get_text(strip=True) if title_elem else None
    
    if not title:
        return None
    
    # Find date
    date_elem = container.select_one('time, [class*="date"], [datetime]')
    published_date = None
    if date_elem:
        # Try datetime attribute first
        published_date = date_elem.get('datetime')
        if not published_date:
            published_date = date_elem.get_text(strip=True)
    
    # Find summary/subtitle
    summary_elem = container.select_one('[class*="subtitle"], [class*="preview"], [class*="description"], p')
    summary = summary_elem.get_text(strip=True) if summary_elem else None
    
    return {
        'title': title,
        'url': url,
        'published_date': published_date,
        'summary': summary
    }


def fetch_post_content(url: str) -> Optional[str]:
    """Fetch the full content of a single post."""
    html = fetch_page(url)
    if not html:
        return None
    
    soup = BeautifulSoup(html, "lxml")
    
    # Substack post content is usually in a div with class containing 'body' or 'post-content'
    content_selectors = [
        'div[class*="body-markup"]',
        'div[class*="post-content"]',
        'div[class*="available-content"]',
        'article div[class*="body"]',
        '.post-content',
        'article'
    ]
    
    for selector in content_selectors:
        content_elem = soup.select_one(selector)
        if content_elem:
            return str(content_elem)
    
    return None


def scrape_archive(fetch_content: bool = True, max_posts: Optional[int] = None) -> list[dict]:
    """
    Scrape the entire Substack archive.
    
    Args:
        fetch_content: If True, also fetch full content for each post
        max_posts: Maximum number of posts to scrape (None for all)
    
    Returns:
        List of post dictionaries
    """
    print(f"Fetching archive from {ARCHIVE_URL}...")
    
    all_posts = []
    page_num = 0
    
    # Substack archives can be paginated or use infinite scroll with API
    # First, try the main archive page
    html = fetch_page(ARCHIVE_URL)
    if not html:
        print("Failed to fetch archive page")
        return []
    
    posts = parse_archive_page(html)
    print(f"Found {len(posts)} posts on archive page")
    
    # Try to find more posts via Substack's API endpoint
    # Substack uses /api/v1/archive endpoint for pagination
    api_url = f"{SUBSTACK_URL}/api/v1/archive"
    offset = 0
    limit = 12
    
    while True:
        try:
            params = {"sort": "new", "offset": offset, "limit": limit}
            response = requests.get(api_url, params=params, headers=HEADERS, timeout=30)
            
            if response.status_code != 200:
                break
                
            data = response.json()
            if not data:
                break
            
            for item in data:
                post = {
                    'title': item.get('title', ''),
                    'url': f"{SUBSTACK_URL}/p/{item.get('slug', '')}",
                    'published_date': item.get('post_date', ''),
                    'summary': item.get('subtitle', '') or item.get('description', ''),
                }
                
                # Avoid duplicates
                if not any(p['url'] == post['url'] for p in posts):
                    posts.append(post)
            
            offset += limit
            time.sleep(0.5)  # Be polite to the API
            
            if max_posts and len(posts) >= max_posts:
                break
                
        except Exception as e:
            print(f"API request failed (this is normal if API is not available): {e}")
            break
    
    print(f"Total posts found: {len(posts)}")
    
    if max_posts:
        posts = posts[:max_posts]
    
    # Fetch full content for each post
    if fetch_content:
        print("Fetching full content for each post...")
        for i, post in enumerate(posts):
            print(f"  [{i+1}/{len(posts)}] {post['title'][:50]}...")
            content = fetch_post_content(post['url'])
            post['content_html'] = content
            post['scraped_at'] = datetime.now(timezone.utc).isoformat()
            time.sleep(REQUEST_DELAY)
    
    return posts


def save_posts(posts: list[dict], output_file: Path = OUTPUT_FILE):
    """Save posts to a JSONL file (one JSON object per line)."""
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for post in posts:
            f.write(json.dumps(post, ensure_ascii=False) + '\n')
    
    print(f"Saved {len(posts)} posts to {output_file}")


def load_posts(input_file: Path = OUTPUT_FILE) -> list[dict]:
    """Load posts from a JSONL file."""
    if not input_file.exists():
        return []
    
    posts = []
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                posts.append(json.loads(line))
    
    return posts


def run_scraper(fetch_content: bool = True, max_posts: Optional[int] = None):
    """Main function to run the scraper."""
    print("=" * 60)
    print("Substack Archive Scraper")
    print(f"Target: {SUBSTACK_URL}")
    print("=" * 60)
    
    posts = scrape_archive(fetch_content=fetch_content, max_posts=max_posts)
    
    if posts:
        save_posts(posts)
        print("\nScraping complete!")
        print(f"Posts saved to: {OUTPUT_FILE}")
    else:
        print("\nNo posts were scraped. Check the archive URL and selectors.")
    
    return posts


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Scrape Substack newsletter archive")
    parser.add_argument("--no-content", action="store_true", 
                        help="Skip fetching full post content (faster)")
    parser.add_argument("--max-posts", type=int, default=None,
                        help="Maximum number of posts to scrape")
    
    args = parser.parse_args()
    
    run_scraper(
        fetch_content=not args.no_content,
        max_posts=args.max_posts
    )

