"""
OpenAI Integration Module

Provides helper functions for AI-powered newsletter optimization suggestions.
Uses the new OpenAI Python SDK client-style API.
"""

import os
import json
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI


# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Default model - can be changed as needed
DEFAULT_MODEL = "gpt-4.1-mini"


# ============================================================================
# System Prompts
# ============================================================================

SYSTEM_PROMPT = """You are an expert newsletter editor for a Substack audience of journalists, editors, and media decision-makers interested in AI, regulation, and the future of news.

Your role is to help optimize newsletters for higher open rates and engagement without resorting to clickbait or sensationalism.

Key principles:
- Be provocative but honest - challenge assumptions without misleading
- Speak to media professionals - they're sophisticated and skeptical
- Connect AI developments to real newsroom concerns
- Balance urgency with credibility
- Use concrete specifics over vague claims
- Consider global perspectives, especially Global South and media systems beyond US/UK

Your suggestions should feel authentic to a thoughtful journalist voice, not like generic marketing copy."""


def build_user_prompt(
    title: str,
    preview: str,
    body: str,
    best_examples: list[dict],
    additional_context: str = ""
) -> str:
    """Build the user prompt for newsletter improvement suggestions."""
    
    # Format best examples
    examples_text = ""
    if best_examples:
        examples_text = "\n\n## MY TOP PERFORMING NEWSLETTERS (for style reference):\n"
        for i, ex in enumerate(best_examples, 1):
            open_rate = ex.get('open_rate', 0)
            if isinstance(open_rate, (int, float)) and open_rate < 1:
                open_rate_str = f"{open_rate:.0%}"
            else:
                open_rate_str = str(open_rate)
            
            examples_text += f"""
{i}. "{ex.get('title', 'Untitled')}"
   Open rate: {open_rate_str}
   Excerpt: {ex.get('content_excerpt', ex.get('summary', 'No excerpt available'))[:200]}...
"""
    
    prompt = f"""## CURRENT DRAFT TO OPTIMIZE:

**Title:** {title}

**Preview/Subtitle:** {preview if preview else "[No preview provided]"}

**Body:**
{body[:3000]}{"..." if len(body) > 3000 else ""}

{examples_text}

{f"## ADDITIONAL CONTEXT: {additional_context}" if additional_context else ""}

## YOUR TASK:

Analyze this newsletter draft and provide optimization suggestions. Return a JSON object with:

1. **headline_suggestions** (array of 5 strings): Alternative headlines, each with a different angle:
   - #1: Provocative but honest - challenges reader assumptions
   - #2: Clear explanatory - tells exactly what they'll learn
   - #3: Pragmatic / "how-to" - actionable focus
   - #4: Global/media-systems angle - if relevant to the content
   - #5: Contrarian - challenges the consensus view

2. **preview_suggestions** (array of 3 strings): Short, sharp preview lines (15-30 words each) that:
   - Create curiosity without clickbait
   - Hint at the value/insight inside
   - Speak directly to media professionals

3. **cta_suggestion** (string): A compelling 2-3 sentence closing call-to-action specifically for journalists and media decision-makers. Should encourage sharing, engagement, or subscription.

4. **body_edit_suggestions** (string): A bullet-pointed list of structural and tonal edits to improve the body, including:
   - Opening hook improvements
   - Structure/flow suggestions  
   - Key points to emphasize or clarify
   - Tone adjustments for the audience
   - Suggested additions or cuts

Return ONLY valid JSON. No additional text or explanation outside the JSON object."""

    return prompt


# ============================================================================
# Main Suggestion Function
# ============================================================================

def suggest_newsletter_improvements(
    title: str,
    preview: str,
    body: str,
    best_examples: list[dict],
    model: str = DEFAULT_MODEL,
    additional_context: str = ""
) -> dict:
    """
    Generate AI suggestions for improving a newsletter draft.
    
    Args:
        title: The current draft title
        preview: The preview/subtitle text
        body: The full body content
        best_examples: List of dicts with keys:
            - 'title': str
            - 'open_rate': float or str
            - 'content_excerpt' or 'summary': str
        model: OpenAI model to use
        additional_context: Optional additional context for the AI
    
    Returns:
        dict with keys:
            - 'headline_suggestions': list[str] (5 alternatives)
            - 'preview_suggestions': list[str] (3 alternatives)
            - 'cta_suggestion': str
            - 'body_edit_suggestions': str
            - 'error': str (if there was an error)
    """
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        return {
            'error': "OpenAI API key not configured. Please set OPENAI_API_KEY in your .env file.",
            'headline_suggestions': [],
            'preview_suggestions': [],
            'cta_suggestion': '',
            'body_edit_suggestions': '',
        }
    
    # Build prompts
    user_prompt = build_user_prompt(title, preview, body, best_examples, additional_context)
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.8,  # Allow some creativity
            max_tokens=2000,
        )
        
        # Parse the response
        content = response.choices[0].message.content
        result = json.loads(content)
        
        # Validate and normalize the response
        return {
            'headline_suggestions': result.get('headline_suggestions', [])[:5],
            'preview_suggestions': result.get('preview_suggestions', [])[:3],
            'cta_suggestion': result.get('cta_suggestion', ''),
            'body_edit_suggestions': result.get('body_edit_suggestions', ''),
            'error': None,
        }
        
    except json.JSONDecodeError as e:
        return {
            'error': f"Failed to parse AI response as JSON: {str(e)}",
            'headline_suggestions': [],
            'preview_suggestions': [],
            'cta_suggestion': '',
            'body_edit_suggestions': '',
            'raw_response': content if 'content' in dir() else None,
        }
    except Exception as e:
        return {
            'error': f"OpenAI API error: {str(e)}",
            'headline_suggestions': [],
            'preview_suggestions': [],
            'cta_suggestion': '',
            'body_edit_suggestions': '',
        }


# ============================================================================
# Additional Helper Functions
# ============================================================================

def check_api_connection() -> tuple[bool, str]:
    """
    Test the OpenAI API connection.
    
    Returns:
        (success: bool, message: str)
    """
    if not os.getenv("OPENAI_API_KEY"):
        return False, "OPENAI_API_KEY not set in environment"
    
    try:
        # Simple test call
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": "Say 'connected' in one word."}],
            max_tokens=10,
        )
        return True, "Connected successfully"
    except Exception as e:
        return False, f"Connection failed: {str(e)}"


def get_content_excerpt(content_html: str, max_length: int = 300) -> str:
    """Extract a clean text excerpt from HTML content."""
    if not content_html:
        return ""
    
    from bs4 import BeautifulSoup
    
    soup = BeautifulSoup(content_html, 'lxml')
    
    # Remove scripts and styles
    for elem in soup(['script', 'style']):
        elem.decompose()
    
    text = soup.get_text(separator=' ', strip=True)
    
    # Truncate to max_length, trying to break at a word boundary
    if len(text) > max_length:
        text = text[:max_length]
        last_space = text.rfind(' ')
        if last_space > max_length * 0.8:
            text = text[:last_space]
        text += "..."
    
    return text


def prepare_best_examples(df, n: int = 5) -> list[dict]:
    """
    Prepare top N newsletters as examples for the AI prompt.
    
    Args:
        df: DataFrame with newsletter data (must have 'open_rate' column)
        n: Number of top examples to return
    
    Returns:
        List of dicts with 'title', 'open_rate', 'content_excerpt'
    """
    if df is None or df.empty:
        return []
    
    if 'open_rate' not in df.columns:
        return []
    
    # Get top N by open rate
    valid_df = df[df['open_rate'].notna()].copy()
    top_n = valid_df.nlargest(n, 'open_rate')
    
    examples = []
    for _, row in top_n.iterrows():
        example = {
            'title': row.get('title', 'Untitled'),
            'open_rate': row.get('open_rate', 0),
        }
        
        # Try to get an excerpt
        if 'content_html' in row and row['content_html']:
            example['content_excerpt'] = get_content_excerpt(row['content_html'])
        elif 'summary' in row and row['summary']:
            example['content_excerpt'] = row['summary']
        else:
            example['content_excerpt'] = ""
        
        examples.append(example)
    
    return examples


# ============================================================================
# Test Function
# ============================================================================

if __name__ == "__main__":
    print("Testing OpenAI connection...")
    success, message = check_api_connection()
    print(f"Connection test: {'✓' if success else '✗'} {message}")
    
    if success:
        print("\nTesting suggestion generation...")
        result = suggest_newsletter_improvements(
            title="AI is changing newsrooms faster than we thought",
            preview="What the latest tools mean for journalism",
            body="Newsrooms around the world are adopting AI tools at an unprecedented pace. From automated transcription to AI-assisted fact-checking, these technologies are reshaping how journalists work. But what does this mean for the future of the profession?",
            best_examples=[
                {
                    'title': 'The EU AI Act: What journalists need to know',
                    'open_rate': 0.28,
                    'content_excerpt': 'The new regulation will have major implications...'
                }
            ]
        )
        
        if result.get('error'):
            print(f"Error: {result['error']}")
        else:
            print("\nHeadline suggestions:")
            for i, h in enumerate(result.get('headline_suggestions', []), 1):
                print(f"  {i}. {h}")
            
            print("\nPreview suggestions:")
            for i, p in enumerate(result.get('preview_suggestions', []), 1):
                print(f"  {i}. {p}")
            
            print(f"\nCTA suggestion:\n  {result.get('cta_suggestion', 'N/A')}")









