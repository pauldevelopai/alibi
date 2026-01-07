"""
Image Service - AI Image Generation and Search

Provides:
- DALL-E image generation
- Unsplash image search (free, attribution required)
- Pexels image search (free, attribution required)
"""

import os
import base64
import requests
from pathlib import Path
from typing import Optional
from urllib.parse import quote

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Try to import usage logging
try:
    from openai_dashboard import log_api_call
    USAGE_LOGGING_AVAILABLE = True
except ImportError:
    USAGE_LOGGING_AVAILABLE = False
    def log_api_call(*args, **kwargs):
        pass

# OpenAI client for DALL-E
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# API keys for image search services
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY", "")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")

# Image storage directory
IMAGES_DIR = Path(__file__).parent / "generated_images"
IMAGES_DIR.mkdir(exist_ok=True)


# ============================================================================
# DALL-E Image Generation
# ============================================================================

def generate_image_dalle(
    prompt: str,
    style: str = "vivid",
    size: str = "1792x1024",  # Wide format good for newsletters
    quality: str = "standard",
    model: str = "dall-e-3"
) -> dict:
    """
    Generate an image using DALL-E 3.
    
    Args:
        prompt: Description of the image to generate
        style: "vivid" (dramatic) or "natural" (realistic)
        size: "1024x1024", "1792x1024" (wide), or "1024x1792" (tall)
        quality: "standard" or "hd"
        model: "dall-e-3" or "dall-e-2"
    
    Returns:
        dict with 'url', 'revised_prompt', 'error'
    """
    if not os.getenv("OPENAI_API_KEY"):
        return {'error': 'OpenAI API key not configured'}
    
    try:
        # Enhance prompt for newsletter context
        enhanced_prompt = f"""Create a professional, editorial-style image for a newsletter about AI and media.

{prompt}

Style notes:
- Modern, clean aesthetic
- Suitable for professional journalism newsletter
- Avoid clichéd AI imagery (no blue glowing brains or binary code)
- Focus on human elements and real-world impact
- Editorial photography or illustration style"""

        response = client.images.generate(
            model=model,
            prompt=enhanced_prompt,
            size=size,
            quality=quality,
            style=style,
            n=1,
        )
        
        # Log API usage
        if USAGE_LOGGING_AVAILABLE:
            log_api_call(
                model=model,
                feature="image_generation",
                is_image=True,
                image_size=size,
                image_quality=quality
            )
        
        image_url = response.data[0].url
        revised_prompt = response.data[0].revised_prompt
        
        return {
            'url': image_url,
            'revised_prompt': revised_prompt,
            'source': 'dalle',
            'attribution': None,  # No attribution needed for DALL-E
        }
        
    except Exception as e:
        return {'error': f'DALL-E generation failed: {str(e)}'}


def suggest_image_prompts(topic: str, story_type: str = "") -> list[str]:
    """
    Generate suggested image prompts for a newsletter topic.
    
    Args:
        topic: The newsletter topic/idea
        story_type: The type of story (how_to, news_analysis, etc.)
    
    Returns:
        List of suggested prompts
    """
    if not os.getenv("OPENAI_API_KEY"):
        return [f"Editorial image representing: {topic}"]
    
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system",
                    "content": """You are an art director for a newsletter about AI and media.
Generate 4 diverse image prompt ideas for DALL-E.

Focus on:
- Editorial photography style
- Human elements and real-world impact
- African/Global South perspectives when relevant
- Avoiding AI clichés (no blue glowing brains, matrix code, robot hands)
- Professional, journalistic aesthetic

Return each prompt on a new line, numbered 1-4."""
                },
                {
                    "role": "user",
                    "content": f"Newsletter topic: {topic}\nStory type: {story_type}\n\nGenerate 4 image prompts:"
                }
            ],
            temperature=0.8,
            max_tokens=500,
        )
        
        content = response.choices[0].message.content
        
        # Parse numbered prompts
        prompts = []
        for line in content.split('\n'):
            line = line.strip()
            if line and line[0].isdigit():
                # Remove number prefix
                prompt = line.lstrip('0123456789.):- ').strip()
                if prompt:
                    prompts.append(prompt)
        
        return prompts if prompts else [f"Editorial image for: {topic}"]
        
    except Exception as e:
        return [f"Editorial image for: {topic}"]


# ============================================================================
# Unsplash Image Search
# ============================================================================

def search_unsplash(
    query: str,
    per_page: int = 10,
    orientation: str = "landscape"
) -> dict:
    """
    Search for images on Unsplash.
    
    Args:
        query: Search terms
        per_page: Number of results (max 30)
        orientation: "landscape", "portrait", or "squarish"
    
    Returns:
        dict with 'images' list and 'error' if any
    """
    if not UNSPLASH_ACCESS_KEY:
        return {'error': 'Unsplash API key not configured. Add UNSPLASH_ACCESS_KEY to .env', 'images': []}
    
    try:
        url = "https://api.unsplash.com/search/photos"
        headers = {
            "Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"
        }
        params = {
            "query": query,
            "per_page": per_page,
            "orientation": orientation,
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        images = []
        for photo in data.get('results', []):
            images.append({
                'id': photo['id'],
                'url_small': photo['urls']['small'],
                'url_regular': photo['urls']['regular'],
                'url_full': photo['urls']['full'],
                'url_raw': photo['urls']['raw'],
                'description': photo.get('description') or photo.get('alt_description', ''),
                'photographer': photo['user']['name'],
                'photographer_url': photo['user']['links']['html'],
                'source': 'unsplash',
                'download_url': photo['links']['download'],
                'attribution': f'Photo by {photo["user"]["name"]} on Unsplash',
                'attribution_html': f'Photo by <a href="{photo["user"]["links"]["html"]}?utm_source=newsletter_optimizer&utm_medium=referral">{photo["user"]["name"]}</a> on <a href="https://unsplash.com/?utm_source=newsletter_optimizer&utm_medium=referral">Unsplash</a>',
            })
        
        return {
            'images': images,
            'total': data.get('total', 0),
            'total_pages': data.get('total_pages', 0),
        }
        
    except requests.exceptions.RequestException as e:
        return {'error': f'Unsplash search failed: {str(e)}', 'images': []}


# ============================================================================
# Pexels Image Search
# ============================================================================

def search_pexels(
    query: str,
    per_page: int = 10,
    orientation: str = "landscape"
) -> dict:
    """
    Search for images on Pexels.
    
    Args:
        query: Search terms
        per_page: Number of results (max 80)
        orientation: "landscape", "portrait", or "square"
    
    Returns:
        dict with 'images' list and 'error' if any
    """
    if not PEXELS_API_KEY:
        return {'error': 'Pexels API key not configured. Add PEXELS_API_KEY to .env', 'images': []}
    
    try:
        url = "https://api.pexels.com/v1/search"
        headers = {
            "Authorization": PEXELS_API_KEY
        }
        params = {
            "query": query,
            "per_page": per_page,
            "orientation": orientation,
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        images = []
        for photo in data.get('photos', []):
            images.append({
                'id': photo['id'],
                'url_small': photo['src']['small'],
                'url_regular': photo['src']['medium'],
                'url_full': photo['src']['large'],
                'url_original': photo['src']['original'],
                'description': photo.get('alt', ''),
                'photographer': photo['photographer'],
                'photographer_url': photo['photographer_url'],
                'source': 'pexels',
                'download_url': photo['src']['original'],
                'attribution': f'Photo by {photo["photographer"]} on Pexels',
                'attribution_html': f'Photo by <a href="{photo["photographer_url"]}">{photo["photographer"]}</a> on <a href="https://www.pexels.com">Pexels</a>',
            })
        
        return {
            'images': images,
            'total': data.get('total_results', 0),
        }
        
    except requests.exceptions.RequestException as e:
        return {'error': f'Pexels search failed: {str(e)}', 'images': []}


# ============================================================================
# Combined Search
# ============================================================================

def search_images(
    query: str,
    sources: list[str] = ["unsplash", "pexels"],
    per_source: int = 6,
    orientation: str = "landscape"
) -> dict:
    """
    Search for images across multiple sources.
    
    Args:
        query: Search terms
        sources: List of sources to search ("unsplash", "pexels")
        per_source: Number of results per source
        orientation: "landscape", "portrait", or "square"
    
    Returns:
        dict with 'images' list from all sources
    """
    all_images = []
    errors = []
    
    if "unsplash" in sources:
        result = search_unsplash(query, per_page=per_source, orientation=orientation)
        if result.get('images'):
            all_images.extend(result['images'])
        if result.get('error'):
            errors.append(result['error'])
    
    if "pexels" in sources:
        result = search_pexels(query, per_page=per_source, orientation=orientation)
        if result.get('images'):
            all_images.extend(result['images'])
        if result.get('error'):
            errors.append(result['error'])
    
    return {
        'images': all_images,
        'total': len(all_images),
        'errors': errors if errors else None,
    }


def get_search_suggestions(topic: str) -> list[str]:
    """
    Generate search term suggestions for finding images.
    
    Args:
        topic: The newsletter topic
    
    Returns:
        List of suggested search terms
    """
    # Common AI/tech/media related search modifiers
    base_terms = []
    
    # Extract key concepts from topic
    topic_lower = topic.lower()
    
    # Add topic-based suggestions
    base_terms.append(topic[:50])  # Truncated topic
    
    # Add relevant modifiers based on content
    if 'africa' in topic_lower:
        base_terms.extend(['African technology', 'Africa business', 'African professionals'])
    
    if 'ai' in topic_lower or 'artificial' in topic_lower:
        base_terms.extend(['technology future', 'digital innovation', 'computer workspace'])
    
    if 'media' in topic_lower or 'news' in topic_lower or 'journalism' in topic_lower:
        base_terms.extend(['newsroom', 'journalist working', 'media technology'])
    
    if 'law' in topic_lower or 'regulation' in topic_lower or 'legal' in topic_lower:
        base_terms.extend(['legal technology', 'courtroom', 'law books'])
    
    if 'podcast' in topic_lower or 'audio' in topic_lower:
        base_terms.extend(['podcast studio', 'microphone recording', 'audio production'])
    
    # Always include some general options
    base_terms.extend([
        'technology innovation',
        'diverse professionals',
        'future workplace',
    ])
    
    # Remove duplicates while preserving order
    seen = set()
    unique_terms = []
    for term in base_terms:
        if term.lower() not in seen:
            seen.add(term.lower())
            unique_terms.append(term)
    
    return unique_terms[:8]


# ============================================================================
# API Status Check
# ============================================================================

def check_image_services() -> dict:
    """Check which image services are available."""
    return {
        'dalle': bool(os.getenv("OPENAI_API_KEY")),
        'unsplash': bool(UNSPLASH_ACCESS_KEY),
        'pexels': bool(PEXELS_API_KEY),
    }


# ============================================================================
# Test
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("IMAGE SERVICE TEST")
    print("=" * 60)
    
    status = check_image_services()
    print(f"\nService Status:")
    print(f"  DALL-E: {'✓' if status['dalle'] else '✗'}")
    print(f"  Unsplash: {'✓' if status['unsplash'] else '✗'}")
    print(f"  Pexels: {'✓' if status['pexels'] else '✗'}")
    
    # Test search suggestions
    print("\nSearch suggestions for 'AI in African newsrooms':")
    suggestions = get_search_suggestions("AI in African newsrooms")
    for s in suggestions:
        print(f"  - {s}")
    
    # Test image search if available
    if status['unsplash']:
        print("\nTesting Unsplash search...")
        result = search_unsplash("African technology", per_page=3)
        if result.get('images'):
            print(f"  Found {len(result['images'])} images")
            for img in result['images'][:3]:
                print(f"    - {img['photographer']}: {img['description'][:50] if img['description'] else 'No description'}")
        else:
            print(f"  Error: {result.get('error')}")
    
    # Test DALL-E prompt suggestions
    if status['dalle']:
        print("\nGenerating image prompt suggestions...")
        prompts = suggest_image_prompts("AI replacing news anchors in Africa", "news_analysis")
        for p in prompts:
            print(f"  - {p[:80]}...")


