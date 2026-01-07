"""
Publishing Analytics Module for Letter+

Analyzes newsletter performance data to:
1. Find optimal publishing day/time
2. Generate social media posts for distribution
3. Track performance trends
4. Provide publishing recommendations
"""

import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple
import re

# Try to import pandas for analytics
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

# Try to import OpenAI for social post generation
try:
    from openai import OpenAI
    from dotenv import load_dotenv
    load_dotenv()
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    OPENAI_AVAILABLE = True
except:
    OPENAI_AVAILABLE = False

# Paths
DATA_DIR = Path(__file__).parent / "data"
STATS_FILE = DATA_DIR / "newsletters_with_stats.csv"
PUBLISHING_HISTORY_FILE = DATA_DIR / "publishing_history.json"


# ============================================================================
# Data Loading
# ============================================================================

def load_newsletter_stats() -> Optional[pd.DataFrame]:
    """Load newsletter statistics from CSV."""
    if not PANDAS_AVAILABLE:
        return None
    
    if not STATS_FILE.exists():
        return None
    
    try:
        df = pd.read_csv(STATS_FILE)
        df = df.dropna(subset=['date'])
        df['date'] = pd.to_datetime(df['date'])
        df['day_of_week'] = df['date'].dt.day_name()
        df['month'] = df['date'].dt.month_name()
        df['hour'] = df['date'].dt.hour if 'hour' in df.columns else 10  # Default to 10am
        return df
    except Exception as e:
        print(f"Error loading stats: {e}")
        return None


def load_publishing_history() -> dict:
    """Load publishing history."""
    if PUBLISHING_HISTORY_FILE.exists():
        with open(PUBLISHING_HISTORY_FILE, 'r') as f:
            return json.load(f)
    return {'posts': [], 'social_shares': []}


def save_publishing_history(history: dict):
    """Save publishing history."""
    with open(PUBLISHING_HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2, default=str)


# ============================================================================
# Analytics Functions
# ============================================================================

def analyze_best_publishing_day() -> dict:
    """
    Analyze which day of the week gets the best engagement.
    
    Returns dict with:
    - best_day: The recommended day
    - day_stats: Stats for each day
    - confidence: How confident we are (based on sample size)
    """
    df = load_newsletter_stats()
    
    if df is None or len(df) < 5:
        return {
            'best_day': 'Tuesday',
            'confidence': 'low',
            'reason': 'Not enough data - using industry best practices',
            'day_stats': {},
            'recommendation': 'Tuesday or Wednesday mornings typically perform best for B2B newsletters.'
        }
    
    # Group by day of week
    day_stats = df.groupby('day_of_week').agg({
        'open_rate': ['mean', 'std', 'count'],
        'opens': ['mean', 'sum']
    }).round(4)
    
    # Flatten column names
    day_stats.columns = ['avg_open_rate', 'std_open_rate', 'count', 'avg_opens', 'total_opens']
    day_stats = day_stats.reset_index()
    
    # Find best day (by average open rate, weighted by sample size)
    # Only consider days with at least 3 newsletters
    significant_days = day_stats[day_stats['count'] >= 3]
    
    if len(significant_days) == 0:
        # Not enough data per day
        best_row = day_stats.loc[day_stats['avg_open_rate'].idxmax()]
        confidence = 'low'
    else:
        best_row = significant_days.loc[significant_days['avg_open_rate'].idxmax()]
        confidence = 'high' if best_row['count'] >= 10 else 'medium'
    
    best_day = best_row['day_of_week']
    
    # Build day stats dict
    stats_dict = {}
    for _, row in day_stats.iterrows():
        stats_dict[row['day_of_week']] = {
            'avg_open_rate': float(row['avg_open_rate']),
            'count': int(row['count']),
            'avg_opens': int(row['avg_opens'])
        }
    
    # Calculate improvement potential
    worst_day = day_stats.loc[day_stats['avg_open_rate'].idxmin()]
    improvement = ((best_row['avg_open_rate'] - worst_day['avg_open_rate']) / worst_day['avg_open_rate'] * 100)
    
    return {
        'best_day': best_day,
        'best_day_open_rate': float(best_row['avg_open_rate']),
        'best_day_sample_size': int(best_row['count']),
        'confidence': confidence,
        'day_stats': stats_dict,
        'improvement_potential': f"{improvement:.1f}%",
        'recommendation': f"Publishing on {best_day} shows {best_row['avg_open_rate']*100:.1f}% average open rate based on {int(best_row['count'])} newsletters.",
        'worst_day': worst_day['day_of_week'],
        'worst_day_open_rate': float(worst_day['avg_open_rate'])
    }


def analyze_performance_trends() -> dict:
    """
    Analyze performance trends over time.
    
    Returns:
    - trend: 'improving', 'stable', or 'declining'
    - recent_avg: Average of last 5 newsletters
    - overall_avg: Overall average
    - top_performers: Top 5 newsletters
    - insights: List of observations
    """
    df = load_newsletter_stats()
    
    if df is None or len(df) < 5:
        return {
            'trend': 'unknown',
            'insights': ['Not enough data to analyze trends'],
            'recent_avg': 0,
            'overall_avg': 0,
            'top_performers': []
        }
    
    # Sort by date
    df = df.sort_values('date', ascending=False)
    
    # Recent vs historical
    recent = df.head(5)['open_rate'].mean()
    historical = df.tail(len(df) - 5)['open_rate'].mean() if len(df) > 5 else recent
    overall = df['open_rate'].mean()
    
    # Determine trend
    if recent > historical * 1.05:
        trend = 'improving'
        trend_description = f"Your recent newsletters are performing {((recent/historical)-1)*100:.1f}% better than earlier ones."
    elif recent < historical * 0.95:
        trend = 'declining'
        trend_description = f"Your recent newsletters are performing {((1-(recent/historical)))*100:.1f}% below your historical average."
    else:
        trend = 'stable'
        trend_description = "Your newsletter performance has been consistent."
    
    # Top performers
    top5 = df.nlargest(5, 'open_rate')[['title', 'date', 'open_rate', 'opens']].to_dict('records')
    
    # Generate insights
    insights = [trend_description]
    
    # Check for day patterns
    day_analysis = analyze_best_publishing_day()
    if day_analysis['confidence'] in ['medium', 'high']:
        insights.append(f"Best performing day: {day_analysis['best_day']} ({day_analysis['best_day_open_rate']*100:.1f}% open rate)")
    
    # Check for topic patterns in top performers
    top_titles = [t['title'].lower() for t in top5]
    if any('ai' in t and 'africa' in t for t in top_titles):
        insights.append("Newsletters combining AI with Africa/regional focus tend to perform well.")
    if any('how to' in t for t in top_titles):
        insights.append("How-to and tutorial content drives high engagement.")
    
    return {
        'trend': trend,
        'trend_description': trend_description,
        'recent_avg': float(recent),
        'overall_avg': float(overall),
        'historical_avg': float(historical),
        'top_performers': top5,
        'insights': insights,
        'total_newsletters': len(df),
        'total_opens': int(df['opens'].sum()),
        'avg_opens': int(df['opens'].mean())
    }


def get_publishing_recommendation() -> dict:
    """
    Get a comprehensive publishing recommendation.
    
    Combines day analysis, trend analysis, and best practices.
    """
    day_analysis = analyze_best_publishing_day()
    trend_analysis = analyze_performance_trends()
    
    # Build recommendation
    recommendations = []
    
    # Day recommendation
    recommendations.append({
        'type': 'day',
        'title': f"Publish on {day_analysis['best_day']}",
        'description': day_analysis['recommendation'],
        'confidence': day_analysis['confidence'],
        'impact': 'high'
    })
    
    # Time recommendation (based on best practices - we don't have time data)
    recommendations.append({
        'type': 'time',
        'title': "Publish between 9-11 AM",
        'description': "Morning sends typically see 20-30% higher open rates for professional audiences.",
        'confidence': 'medium',
        'impact': 'medium'
    })
    
    # Content recommendations based on top performers
    if trend_analysis['top_performers']:
        top = trend_analysis['top_performers'][0]
        recommendations.append({
            'type': 'content',
            'title': "Use specific, intriguing headlines",
            'description': f"Your best performer '{top['title'][:50]}...' had {top['open_rate']*100:.1f}% open rate.",
            'confidence': 'high',
            'impact': 'high'
        })
    
    # Social timing recommendation
    recommendations.append({
        'type': 'social',
        'title': "Share on social within 1 hour of publish",
        'description': "Initial social shares drive 15-25% of newsletter traffic. Share on LinkedIn, Twitter/X, and relevant communities.",
        'confidence': 'medium',
        'impact': 'medium'
    })
    
    return {
        'recommendations': recommendations,
        'optimal_publish_time': {
            'day': day_analysis['best_day'],
            'time': '10:00 AM',
            'timezone': 'Your local timezone'
        },
        'day_analysis': day_analysis,
        'trend_analysis': trend_analysis
    }


# ============================================================================
# Social Media Post Generation
# ============================================================================

def generate_social_posts(
    headline: str,
    preview: str,
    newsletter_url: str = "",
    key_points: List[str] = None,
    platforms: List[str] = None
) -> dict:
    """
    Generate social media posts to promote the newsletter.
    
    Platforms: twitter, linkedin, threads, bluesky
    """
    if platforms is None:
        platforms = ['twitter', 'linkedin', 'threads']
    
    if not OPENAI_AVAILABLE:
        return {
            'error': 'OpenAI not available for post generation',
            'posts': {}
        }
    
    key_points_text = ""
    if key_points:
        key_points_text = "\n".join([f"- {p}" for p in key_points[:5]])
    
    prompt = f"""Generate social media posts to promote this newsletter issue.

NEWSLETTER:
Headline: {headline}
Preview: {preview}
URL: {newsletter_url or '[NEWSLETTER_URL]'}

KEY POINTS:
{key_points_text or 'Not provided'}

Generate posts for each platform. Be authentic, engaging, and match the platform's style:

1. TWITTER/X (max 280 chars):
- Punchy, direct, maybe provocative
- Use 1-2 relevant hashtags
- Include the URL at the end

2. LINKEDIN (max 700 chars):
- Professional but personal
- Ask a question or share an insight
- Can be longer and more thoughtful
- Include URL

3. THREADS (max 500 chars):
- Conversational, like talking to friends
- Can be slightly more casual than LinkedIn
- Include URL

Format your response as JSON:
{{
    "twitter": "...",
    "linkedin": "...",
    "threads": "..."
}}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a social media expert helping promote newsletters. Write authentic, engaging posts that drive clicks."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=1000
        )
        
        content = response.choices[0].message.content
        
        # Try to parse as JSON
        try:
            # Find JSON in the response
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                posts = json.loads(json_match.group())
            else:
                posts = {'raw': content}
        except:
            posts = {'raw': content}
        
        return {
            'posts': posts,
            'headline': headline,
            'url': newsletter_url,
            'generated_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'error': str(e),
            'posts': {}
        }


def generate_thread_content(
    headline: str,
    preview: str,
    content: str,
    platform: str = 'twitter'
) -> dict:
    """
    Generate a thread (multiple connected posts) for Twitter/X or Threads.
    
    Breaks down the newsletter into a compelling thread.
    """
    if not OPENAI_AVAILABLE:
        return {'error': 'OpenAI not available', 'thread': []}
    
    # Truncate content if too long
    content_preview = content[:3000] if len(content) > 3000 else content
    
    prompt = f"""Create a compelling thread to promote this newsletter on {platform}.

NEWSLETTER:
Headline: {headline}
Preview: {preview}

CONTENT PREVIEW:
{content_preview}

Create a 5-7 tweet thread that:
1. Opens with a hook that stops the scroll
2. Teases the main insights without giving everything away
3. Ends with a CTA to read the full newsletter

For Twitter: Each tweet max 280 chars
For Threads: Each post max 500 chars

Format as JSON array:
["Tweet 1", "Tweet 2", "Tweet 3", ...]
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a viral thread writer. Create engaging threads that make people want to read the full newsletter."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=1500
        )
        
        content = response.choices[0].message.content
        
        # Parse the thread
        try:
            json_match = re.search(r'\[[\s\S]*\]', content)
            if json_match:
                thread = json.loads(json_match.group())
            else:
                thread = [content]
        except:
            thread = [content]
        
        return {
            'thread': thread,
            'platform': platform,
            'headline': headline,
            'generated_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {'error': str(e), 'thread': []}


# ============================================================================
# Publishing Checklist
# ============================================================================

def get_publishing_checklist(newsletter_data: dict = None) -> List[dict]:
    """
    Get a publishing checklist for the newsletter.
    
    Returns list of checklist items with status.
    """
    checklist = [
        {
            'id': 'headline',
            'title': 'Compelling headline',
            'description': 'Is your headline specific and intriguing?',
            'status': 'complete' if newsletter_data and newsletter_data.get('headline') else 'pending'
        },
        {
            'id': 'preview',
            'title': 'Preview text',
            'description': 'Preview text that appears in email clients',
            'status': 'complete' if newsletter_data and newsletter_data.get('preview') else 'pending'
        },
        {
            'id': 'content',
            'title': 'Content proofread',
            'description': 'Check for typos, broken links, formatting',
            'status': 'pending'
        },
        {
            'id': 'images',
            'title': 'Header image',
            'description': 'Eye-catching header image for social shares',
            'status': 'complete' if newsletter_data and newsletter_data.get('image_url') else 'pending'
        },
        {
            'id': 'social_posts',
            'title': 'Social media posts ready',
            'description': 'Prepare posts for Twitter, LinkedIn, Threads',
            'status': 'pending'
        },
        {
            'id': 'timing',
            'title': 'Optimal timing',
            'description': 'Schedule for best engagement day/time',
            'status': 'pending'
        },
        {
            'id': 'test_send',
            'title': 'Test email sent',
            'description': 'Send test to yourself to check formatting',
            'status': 'pending'
        }
    ]
    
    return checklist


# ============================================================================
# Module Info
# ============================================================================

def get_module_status() -> dict:
    """Get the status of this module and its dependencies."""
    return {
        'pandas_available': PANDAS_AVAILABLE,
        'openai_available': OPENAI_AVAILABLE,
        'stats_file_exists': STATS_FILE.exists(),
        'newsletter_count': len(load_newsletter_stats()) if PANDAS_AVAILABLE and STATS_FILE.exists() else 0
    }




