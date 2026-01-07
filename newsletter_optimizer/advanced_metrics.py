"""
Advanced Content Metrics Analyzer

Analyzes 20+ sophisticated patterns in newsletter content:
- Tone (doom vs optimism)
- Humor usage
- Research depth
- Personal voice
- Call to action strength
- Urgency level
- Global perspective
- Practical vs theoretical
- And many more...

Each metric is scored 0-100 and correlated with open rates.
"""

import json
import re
from pathlib import Path
from collections import Counter
from typing import Optional

import pandas as pd
from bs4 import BeautifulSoup


DATA_DIR = Path(__file__).parent / "data"
METRICS_FILE = DATA_DIR / "advanced_metrics.json"


# ============================================================================
# Text Utilities
# ============================================================================

def html_to_text(html: str) -> str:
    """Convert HTML to plain text."""
    if not html:
        return ""
    soup = BeautifulSoup(html, 'lxml')
    for elem in soup(['script', 'style']):
        elem.decompose()
    return soup.get_text(separator=' ', strip=True)


def count_pattern(text: str, patterns: list[str]) -> int:
    """Count occurrences of patterns in text (case insensitive)."""
    text_lower = text.lower()
    return sum(text_lower.count(p.lower()) for p in patterns)


def has_pattern(text: str, patterns: list[str]) -> bool:
    """Check if any pattern exists in text."""
    text_lower = text.lower()
    return any(p.lower() in text_lower for p in patterns)


# ============================================================================
# The 20+ Metrics
# ============================================================================

METRIC_DEFINITIONS = {
    # === TONE METRICS ===
    'doom_level': {
        'name': 'Doom Level',
        'description': 'How apocalyptic/negative is the content?',
        'category': 'tone',
        'keywords_high': [
            'destroy', 'collapse', 'disaster', 'apocalypse', 'crisis', 'threat',
            'danger', 'kill', 'death', 'end of', 'dying', 'catastrophe', 'doom',
            'nightmare', 'horror', 'terrifying', 'alarming', 'devastating'
        ],
        'keywords_low': [
            'opportunity', 'growth', 'improve', 'better', 'solution', 'hope'
        ],
    },
    
    'optimism_level': {
        'name': 'Optimism Level',
        'description': 'How positive/hopeful is the content?',
        'category': 'tone',
        'keywords_high': [
            'opportunity', 'exciting', 'amazing', 'incredible', 'breakthrough',
            'revolution', 'transform', 'empower', 'enable', 'solve', 'improve',
            'better future', 'hope', 'promising', 'potential', 'succeed'
        ],
        'keywords_low': [
            'problem', 'fail', 'threat', 'danger', 'crisis'
        ],
    },
    
    'urgency_level': {
        'name': 'Urgency Level',
        'description': 'How time-sensitive does the content feel?',
        'category': 'tone',
        'keywords_high': [
            'now', 'immediately', 'urgent', 'breaking', 'just happened',
            'this week', 'today', 'must', 'critical', 'act now', 'don\'t wait',
            'time is running out', 'before it\'s too late'
        ],
        'keywords_low': [],
    },
    
    'controversy_level': {
        'name': 'Controversy Level',
        'description': 'How provocative/controversial is the take?',
        'category': 'tone',
        'keywords_high': [
            'wrong', 'mistake', 'lie', 'myth', 'truth is', 'actually',
            'controversial', 'debate', 'disagree', 'unpopular opinion',
            'hot take', 'fight', 'battle', 'war', 'vs', 'against'
        ],
        'keywords_low': [],
    },
    
    # === STYLE METRICS ===
    'humor_usage': {
        'name': 'Humor Usage',
        'description': 'How much humor/wit is used?',
        'category': 'style',
        'keywords_high': [
            'joke', 'funny', 'hilarious', 'laugh', 'lol', 'haha', 'amusing',
            'ridiculous', 'absurd', 'ironic', 'satirical', 'sarcastic',
            '😂', '🤣', 'spoiler:', 'plot twist'
        ],
        'keywords_low': [],
    },
    
    'personal_voice': {
        'name': 'Personal Voice',
        'description': 'How personal/first-person is the writing?',
        'category': 'style',
        'keywords_high': [
            'I think', 'I believe', 'my view', 'in my opinion', 'I\'ve',
            'I was', 'I am', 'I have', 'personally', 'my experience',
            'I noticed', 'I spoke', 'I interviewed', 'I attended'
        ],
        'keywords_low': [],
    },
    
    'storytelling': {
        'name': 'Storytelling',
        'description': 'How narrative-driven is the content?',
        'category': 'style',
        'keywords_high': [
            'story', 'once upon', 'imagine', 'picture this', 'let me tell you',
            'happened', 'journey', 'began', 'ended up', 'discovered',
            'when I', 'one day', 'last week', 'recently'
        ],
        'keywords_low': [],
    },
    
    'conversational_tone': {
        'name': 'Conversational Tone',
        'description': 'How casual/conversational vs formal?',
        'category': 'style',
        'keywords_high': [
            'you', 'you\'re', 'you\'ll', 'let\'s', 'we\'re', 'gonna',
            'isn\'t it', 'right?', 'don\'t you', 'think about it',
            'here\'s the thing', 'look,', 'okay,', 'so,', 'anyway'
        ],
        'keywords_low': [],
    },
    
    # === CONTENT DEPTH METRICS ===
    'research_depth': {
        'name': 'Research Depth',
        'description': 'How well-researched with data/sources?',
        'category': 'depth',
        'keywords_high': [
            'study', 'research', 'data', 'statistics', 'survey', 'report',
            'according to', 'found that', 'percent', '%', 'million',
            'billion', 'analysis', 'evidence', 'source:', 'published'
        ],
        'keywords_low': [],
    },
    
    'expert_citations': {
        'name': 'Expert Citations',
        'description': 'How many experts/sources are quoted?',
        'category': 'depth',
        'keywords_high': [
            'said', 'told me', 'according to', 'explains', 'argues',
            'CEO', 'founder', 'professor', 'researcher', 'expert',
            'analyst', 'director', 'editor', 'journalist'
        ],
        'keywords_low': [],
    },
    
    'technical_depth': {
        'name': 'Technical Depth',
        'description': 'How technical/detailed is the explanation?',
        'category': 'depth',
        'keywords_high': [
            'algorithm', 'model', 'architecture', 'API', 'code', 'technical',
            'implementation', 'framework', 'infrastructure', 'system',
            'database', 'neural network', 'machine learning', 'parameters'
        ],
        'keywords_low': [],
    },
    
    # === PRACTICAL METRICS ===
    'actionability': {
        'name': 'Actionability',
        'description': 'How actionable/practical is the content?',
        'category': 'practical',
        'keywords_high': [
            'how to', 'step', 'guide', 'tutorial', 'tips', 'try this',
            'you can', 'start by', 'here\'s how', 'action', 'implement',
            'use this', 'download', 'sign up', 'click', 'go to'
        ],
        'keywords_low': [],
    },
    
    'tool_focus': {
        'name': 'Tool Focus',
        'description': 'How focused on specific tools/products?',
        'category': 'practical',
        'keywords_high': [
            'ChatGPT', 'OpenAI', 'Claude', 'Gemini', 'Midjourney', 'DALL-E',
            'app', 'tool', 'platform', 'software', 'plugin', 'extension',
            'service', 'product', 'feature', 'update', 'release'
        ],
        'keywords_low': [],
    },
    
    # === GEOGRAPHIC/SCOPE METRICS ===
    'africa_focus': {
        'name': 'Africa Focus',
        'description': 'How focused on African perspectives?',
        'category': 'geographic',
        'keywords_high': [
            'Africa', 'African', 'Nigeria', 'Kenya', 'South Africa', 'Ghana',
            'Tanzania', 'Uganda', 'Zimbabwe', 'Egypt', 'Morocco', 'Ethiopia',
            'Rwanda', 'Namibia', 'Zambia', 'continent'
        ],
        'keywords_low': [],
    },
    
    'global_south_focus': {
        'name': 'Global South Focus',
        'description': 'How focused on Global South perspectives?',
        'category': 'geographic',
        'keywords_high': [
            'Global South', 'developing', 'emerging market', 'Asia', 'India',
            'Latin America', 'Brazil', 'Indonesia', 'Philippines', 'Pakistan',
            'Bangladesh', 'Vietnam', 'Mexico', 'Colombia'
        ],
        'keywords_low': [],
    },
    
    'western_focus': {
        'name': 'Western/Tech Hub Focus',
        'description': 'How focused on US/Europe/Silicon Valley?',
        'category': 'geographic',
        'keywords_high': [
            'Silicon Valley', 'San Francisco', 'New York', 'London', 'EU',
            'European', 'American', 'US', 'UK', 'Google', 'Meta', 'Apple',
            'Microsoft', 'Amazon', 'Tesla', 'startup', 'venture capital'
        ],
        'keywords_low': [],
    },
    
    # === MEDIA INDUSTRY METRICS ===
    'journalism_focus': {
        'name': 'Journalism Focus',
        'description': 'How focused on journalism/newsrooms?',
        'category': 'industry',
        'keywords_high': [
            'journalist', 'newsroom', 'editor', 'reporter', 'news',
            'media', 'publication', 'newspaper', 'broadcast', 'publisher',
            'editorial', 'press', 'correspondent', 'covering'
        ],
        'keywords_low': [],
    },
    
    'regulation_focus': {
        'name': 'Regulation Focus',
        'description': 'How focused on law/regulation/policy?',
        'category': 'industry',
        'keywords_high': [
            'regulation', 'law', 'legal', 'policy', 'government', 'court',
            'lawsuit', 'EU AI Act', 'compliance', 'ban', 'legislation',
            'congress', 'parliament', 'ruling', 'copyright'
        ],
        'keywords_low': [],
    },
    
    # === ENGAGEMENT METRICS ===
    'cta_strength': {
        'name': 'CTA Strength',
        'description': 'How strong are calls to action?',
        'category': 'engagement',
        'keywords_high': [
            'subscribe', 'share', 'forward', 'comment', 'join', 'sign up',
            'click', 'download', 'try', 'check out', 'don\'t miss',
            'let me know', 'reply', 'tell me', 'WhatsApp'
        ],
        'keywords_low': [],
    },
    
    'question_engagement': {
        'name': 'Question Engagement',
        'description': 'How many rhetorical questions are asked?',
        'category': 'engagement',
        'keywords_high': [],  # We count actual question marks
        'keywords_low': [],
    },
    
    # === STRUCTURE METRICS ===
    'list_usage': {
        'name': 'List Usage',
        'description': 'How much are lists/bullets used?',
        'category': 'structure',
        'keywords_high': [],  # Detected via HTML structure
        'keywords_low': [],
    },
    
    'subhead_density': {
        'name': 'Subhead Density',
        'description': 'How many section breaks/subheadings?',
        'category': 'structure',
        'keywords_high': [],  # Detected via HTML structure
        'keywords_low': [],
    },
    
    # === NEW METRICS (10 MORE) ===
    
    'skepticism_level': {
        'name': 'Skepticism Level',
        'description': 'How skeptical/questioning of claims and hype?',
        'category': 'tone',
        'keywords_high': [
            'but', 'however', 'actually', 'really?', 'not so fast', 'wait',
            'skeptical', 'doubt', 'question', 'unclear', 'unproven', 'hype',
            'overhyped', 'not convinced', 'remains to be seen', 'we\'ll see'
        ],
        'keywords_low': [],
    },
    
    'directness': {
        'name': 'Directness',
        'description': 'How direct and blunt vs hedging and diplomatic?',
        'category': 'style',
        'keywords_high': [
            'is', 'will', 'must', 'should', 'clearly', 'obviously', 'simple',
            'the truth is', 'let\'s be honest', 'bluntly', 'frankly', 'fact is',
            'bottom line', 'here it is', 'straight up'
        ],
        'keywords_low': [
            'might', 'maybe', 'perhaps', 'could', 'possibly', 'it seems',
            'arguably', 'somewhat', 'to some extent'
        ],
    },
    
    'specificity': {
        'name': 'Specificity',
        'description': 'How specific with names, numbers, and details?',
        'category': 'depth',
        'keywords_high': [
            'specifically', 'exactly', 'precisely', 'in particular',
            # Numbers and specifics detected separately
        ],
        'keywords_low': [
            'some', 'many', 'various', 'several', 'a lot', 'things',
            'stuff', 'people say', 'they say'
        ],
    },
    
    'forward_looking': {
        'name': 'Forward Looking',
        'description': 'How focused on future vs present/past?',
        'category': 'tone',
        'keywords_high': [
            'will', 'future', 'next year', '2025', '2026', '2027', 'coming',
            'soon', 'expect', 'predict', 'forecast', 'trend', 'emerging',
            'what\'s next', 'looking ahead', 'on the horizon'
        ],
        'keywords_low': [
            'was', 'were', 'used to', 'historically', 'traditional'
        ],
    },
    
    'anecdote_usage': {
        'name': 'Anecdote Usage',
        'description': 'How many personal stories and examples?',
        'category': 'style',
        'keywords_high': [
            'I remember', 'last week', 'yesterday', 'recently I', 'I met',
            'I visited', 'I attended', 'I tried', 'I tested', 'I spoke with',
            'a friend of mine', 'someone I know', 'true story', 'this happened'
        ],
        'keywords_low': [],
    },
    
    'link_density': {
        'name': 'Link Density',
        'description': 'How many external links and references?',
        'category': 'depth',
        'keywords_high': [],  # Detected via HTML
        'keywords_low': [],
    },
    
    'emoji_usage': {
        'name': 'Emoji Usage',
        'description': 'How much emoji/visual elements are used?',
        'category': 'style',
        'keywords_high': [
            '📱', '🔥', '💡', '🚀', '⚠️', '✅', '❌', '🤖', '🎯', '📊',
            '👋', '🏠', '📋', '🎓', '💰', '🌍', '🔧', '📝', '🎉', '👀'
        ],
        'keywords_low': [],
    },
    
    'critique_intensity': {
        'name': 'Critique Intensity',
        'description': 'How critical of tech companies and industry?',
        'category': 'tone',
        'keywords_high': [
            'fail', 'failed', 'flawed', 'broken', 'wrong', 'mistake',
            'terrible', 'awful', 'disappointing', 'poor', 'weak', 'lazy',
            'greedy', 'exploitative', 'harmful', 'dangerous', 'reckless'
        ],
        'keywords_low': [],
    },
    
    'solution_orientation': {
        'name': 'Solution Orientation',
        'description': 'How focused on solutions vs just problems?',
        'category': 'practical',
        'keywords_high': [
            'solution', 'solve', 'fix', 'improve', 'answer', 'way forward',
            'alternative', 'option', 'approach', 'strategy', 'here\'s how',
            'you can', 'try this', 'instead', 'better way'
        ],
        'keywords_low': [],
    },
    
    'audience_acknowledgment': {
        'name': 'Audience Acknowledgment',
        'description': 'How directly addressed is the reader?',
        'category': 'engagement',
        'keywords_high': [
            'you', 'your', 'you\'re', 'you\'ll', 'you\'ve', 'dear reader',
            'my readers', 'subscribers', 'those of you', 'if you\'re',
            'for those who', 'many of you', 'some of you asked'
        ],
        'keywords_low': [],
    },
}


def compute_metric_score(text: str, html: str, metric_key: str) -> float:
    """
    Compute a 0-100 score for a single metric.
    """
    metric = METRIC_DEFINITIONS.get(metric_key, {})
    text_lower = text.lower()
    word_count = len(text.split()) or 1
    
    # Special handling for certain metrics
    if metric_key == 'question_engagement':
        # Count question marks relative to length
        question_count = text.count('?')
        # Normalize: 1 question per 100 words = 50 score
        score = min(100, (question_count / word_count) * 100 * 50)
        return round(score, 1)
    
    if metric_key == 'link_density':
        # Count links in HTML
        if html:
            soup = BeautifulSoup(html, 'lxml')
            links = soup.find_all('a', href=True)
            link_count = len(links)
            # Normalize: 5 links per 500 words = 50 score
            score = min(100, (link_count / word_count) * 500 * 10)
            return round(score, 1)
        return 0
    
    if metric_key == 'specificity':
        # Count numbers and specific patterns
        numbers = len(re.findall(r'\b\d+\b', text))
        proper_nouns = len(re.findall(r'\b[A-Z][a-z]+\b', text))  # Rough estimate
        keywords_high = metric.get('keywords_high', [])
        keywords_low = metric.get('keywords_low', [])
        high_count = count_pattern(text, keywords_high)
        low_count = count_pattern(text, keywords_low)
        
        specificity_score = ((numbers + proper_nouns/10 + high_count) / word_count) * 500
        penalty = (low_count / word_count) * 200
        score = min(100, max(0, specificity_score - penalty))
        return round(score, 1)
    
    if metric_key == 'list_usage':
        # Count list items in HTML
        if html:
            soup = BeautifulSoup(html, 'lxml')
            list_items = len(soup.find_all('li'))
            # Normalize: 10 list items = 100 score
            score = min(100, list_items * 10)
            return round(score, 1)
        return 0
    
    if metric_key == 'subhead_density':
        # Count headings in HTML
        if html:
            soup = BeautifulSoup(html, 'lxml')
            headings = len(soup.find_all(['h2', 'h3', 'h4']))
            # Normalize: 5 headings = 100 score
            score = min(100, headings * 20)
            return round(score, 1)
        return 0
    
    # Default keyword-based scoring
    keywords_high = metric.get('keywords_high', [])
    keywords_low = metric.get('keywords_low', [])
    
    high_count = count_pattern(text, keywords_high)
    low_count = count_pattern(text, keywords_low)
    
    # Calculate density (occurrences per 100 words)
    density = (high_count - low_count * 0.5) / word_count * 100
    
    # Convert to 0-100 score (calibrated so ~2% density = 50)
    score = min(100, max(0, density * 25 + 20))
    
    return round(score, 1)


def compute_all_metrics(title: str, content_html: str) -> dict:
    """
    Compute all 20+ metrics for a single newsletter.
    Returns dict of metric_key -> score (0-100).
    """
    text = html_to_text(content_html) if content_html else ""
    full_text = f"{title} {text}"
    
    scores = {}
    for metric_key in METRIC_DEFINITIONS:
        scores[metric_key] = compute_metric_score(full_text, content_html, metric_key)
    
    return scores


# ============================================================================
# Analyze All Newsletters
# ============================================================================

def load_newsletters_with_stats() -> pd.DataFrame:
    """Load newsletters with their open rates."""
    raw_file = DATA_DIR / "newsletters_raw.jsonl"
    stats_file = DATA_DIR / "newsletters_with_stats.csv"
    
    if not raw_file.exists():
        return pd.DataFrame()
    
    # Load raw newsletters
    newsletters = []
    with open(raw_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                newsletters.append(json.loads(line))
    
    df = pd.DataFrame(newsletters)
    
    # Load stats
    if stats_file.exists():
        stats = pd.read_csv(stats_file)
        stats['_title_key'] = stats['title'].str.strip().str.lower()
        stats_dict = {row['_title_key']: row['open_rate'] for _, row in stats.iterrows()}
        
        df['_title_key'] = df['title'].str.strip().str.lower()
        df['open_rate'] = df['_title_key'].map(stats_dict)
    
    return df


def analyze_all_newsletters() -> dict:
    """
    Analyze all newsletters and compute metrics + correlations.
    Returns comprehensive metrics analysis.
    """
    print("Loading newsletters...")
    df = load_newsletters_with_stats()
    
    if df.empty:
        print("No newsletters found")
        return {}
    
    print(f"Analyzing {len(df)} newsletters...")
    
    # Compute metrics for each newsletter
    all_metrics = []
    
    for idx, row in df.iterrows():
        title = row.get('title', '')
        content = row.get('content_html', '')
        open_rate = row.get('open_rate', None)
        
        metrics = compute_all_metrics(title, content)
        metrics['title'] = title
        metrics['open_rate'] = open_rate
        
        all_metrics.append(metrics)
    
    metrics_df = pd.DataFrame(all_metrics)
    
    # Compute aggregate statistics for each metric
    analysis = {
        'newsletter_count': len(df),
        'metrics': {},
        'correlations': {},
        'recommendations': [],
    }
    
    for metric_key, metric_def in METRIC_DEFINITIONS.items():
        if metric_key in metrics_df.columns:
            values = metrics_df[metric_key]
            
            analysis['metrics'][metric_key] = {
                'name': metric_def['name'],
                'description': metric_def['description'],
                'category': metric_def['category'],
                'mean': round(values.mean(), 1),
                'min': round(values.min(), 1),
                'max': round(values.max(), 1),
                'std': round(values.std(), 1),
            }
            
            # Compute correlation with open rate
            valid_rows = metrics_df[metrics_df['open_rate'].notna()]
            if len(valid_rows) >= 5:
                correlation = valid_rows[metric_key].corr(valid_rows['open_rate'])
                
                analysis['correlations'][metric_key] = {
                    'name': metric_def['name'],
                    'correlation': round(correlation, 3) if not pd.isna(correlation) else 0,
                }
                
                # High vs low comparison
                median = values.median()
                high_group = valid_rows[valid_rows[metric_key] > median]['open_rate']
                low_group = valid_rows[valid_rows[metric_key] <= median]['open_rate']
                
                if len(high_group) > 0 and len(low_group) > 0:
                    diff = high_group.mean() - low_group.mean()
                    analysis['correlations'][metric_key]['high_avg_open_rate'] = round(high_group.mean(), 3)
                    analysis['correlations'][metric_key]['low_avg_open_rate'] = round(low_group.mean(), 3)
                    analysis['correlations'][metric_key]['difference'] = round(diff, 3)
    
    # Sort correlations by impact
    sorted_correlations = sorted(
        analysis['correlations'].items(),
        key=lambda x: abs(x[1].get('difference', 0)),
        reverse=True
    )
    
    # Generate recommendations
    for metric_key, corr_data in sorted_correlations[:10]:
        diff = corr_data.get('difference', 0)
        name = corr_data.get('name', metric_key)
        
        if diff > 0.03:
            analysis['recommendations'].append({
                'metric': metric_key,
                'name': name,
                'impact': f"+{diff*100:.1f}%",
                'recommendation': 'USE MORE',
                'direction': 'positive',
            })
        elif diff < -0.03:
            analysis['recommendations'].append({
                'metric': metric_key,
                'name': name,
                'impact': f"{diff*100:.1f}%",
                'recommendation': 'USE LESS',
                'direction': 'negative',
            })
    
    # Find top performers and their metric profiles
    analysis['top_performers'] = []
    top_df = metrics_df.nlargest(5, 'open_rate')
    
    for _, row in top_df.iterrows():
        profile = {
            'title': row['title'],
            'open_rate': round(row['open_rate'], 3) if pd.notna(row['open_rate']) else None,
            'top_metrics': [],
        }
        
        # Find which metrics are highest for this newsletter
        metric_scores = [(k, row[k]) for k in METRIC_DEFINITIONS.keys() if k in row]
        metric_scores.sort(key=lambda x: x[1], reverse=True)
        
        for metric_key, score in metric_scores[:5]:
            if score > 30:
                profile['top_metrics'].append({
                    'metric': metric_key,
                    'name': METRIC_DEFINITIONS[metric_key]['name'],
                    'score': score,
                })
        
        analysis['top_performers'].append(profile)
    
    return analysis


def convert_to_serializable(obj):
    """Convert numpy types to Python native types for JSON serialization."""
    import numpy as np
    if isinstance(obj, dict):
        return {k: convert_to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_serializable(i) for i in obj]
    elif isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif pd.isna(obj):
        return None
    return obj


def save_analysis(analysis: dict):
    """Save the metrics analysis to file."""
    # Convert numpy types to native Python types
    serializable_analysis = convert_to_serializable(analysis)
    with open(METRICS_FILE, 'w', encoding='utf-8') as f:
        json.dump(serializable_analysis, f, indent=2, ensure_ascii=False)
    print(f"Saved to {METRICS_FILE}")


def load_analysis() -> dict:
    """Load the metrics analysis from file."""
    if not METRICS_FILE.exists():
        return {}
    with open(METRICS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_metric_definitions() -> dict:
    """Return all metric definitions."""
    return METRIC_DEFINITIONS


# ============================================================================
# Main
# ============================================================================

def run_analysis():
    """Run the full advanced metrics analysis."""
    print("=" * 60)
    print("ADVANCED METRICS ANALYZER")
    print(f"Analyzing {len(METRIC_DEFINITIONS)} content metrics")
    print("=" * 60)
    
    analysis = analyze_all_newsletters()
    
    if not analysis:
        print("No data to analyze")
        return None
    
    save_analysis(analysis)
    
    print(f"\n📊 Analyzed {analysis['newsletter_count']} newsletters")
    print(f"📈 Computed {len(analysis['metrics'])} metrics")
    
    print("\n🎯 TOP RECOMMENDATIONS (based on open rate correlation):")
    for rec in analysis['recommendations'][:8]:
        emoji = "✓" if rec['direction'] == 'positive' else "✗"
        print(f"  {emoji} {rec['name']}: {rec['impact']} ({rec['recommendation']})")
    
    print("\n🏆 TOP PERFORMER PROFILES:")
    for tp in analysis['top_performers'][:3]:
        print(f"\n  {tp['title'][:50]}...")
        print(f"    Open rate: {tp['open_rate']:.1%}" if tp['open_rate'] else "    Open rate: N/A")
        print(f"    Strong in: {', '.join(m['name'] for m in tp['top_metrics'][:3])}")
    
    return analysis


if __name__ == "__main__":
    run_analysis()

