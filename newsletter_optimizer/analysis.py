"""
Newsletter Analysis Module

Provides heuristic analysis, pattern extraction, and data merging functionality
for newsletter optimization.
"""

import json
import re
from pathlib import Path
from typing import Optional
from html import unescape

import pandas as pd
import yaml
from bs4 import BeautifulSoup


# Paths
DATA_DIR = Path(__file__).parent / "data"
CONFIG_DIR = Path(__file__).parent / "config"
RAW_DATA_FILE = DATA_DIR / "newsletters_raw.jsonl"
STATS_FILE = DATA_DIR / "newsletters_with_stats.csv"
TOPICS_CONFIG = CONFIG_DIR / "topics_keywords.yml"


def load_config() -> dict:
    """Load topic keywords and other configuration."""
    if TOPICS_CONFIG.exists():
        with open(TOPICS_CONFIG, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    # Default configuration if file doesn't exist
    return {
        'topics': {
            'regulation': ['EU AI Act', 'regulation', 'law', 'lawsuit', 'legal', 'compliance'],
            'media_survival': ['newsroom', 'media', 'journalism', 'journalist', 'publisher'],
            'tools': ['how to', 'tools', 'build', 'tutorial', 'guide'],
            'geopolitics': ['Africa', 'Asia', 'Europe', 'China', 'election', 'global'],
        },
        'strong_verbs': ['destroy', 'implode', 'save', 'endanger', 'collapse', 'transform'],
        'ai_terms': ['AI', 'ChatGPT', 'OpenAI', 'GPT', 'Claude', 'Gemini', 'artificial intelligence'],
    }


CONFIG = load_config()


# ============================================================================
# Data Loading and Merging
# ============================================================================

def load_raw_newsletters(filepath: Path = RAW_DATA_FILE) -> pd.DataFrame:
    """Load scraped newsletter data from JSONL file."""
    if not filepath.exists():
        print(f"Warning: Raw data file not found: {filepath}")
        return pd.DataFrame()
    
    posts = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                posts.append(json.loads(line))
    
    return pd.DataFrame(posts)


def load_stats_csv(filepath: Path = STATS_FILE) -> pd.DataFrame:
    """Load performance stats from CSV file."""
    if not filepath.exists():
        print(f"Warning: Stats file not found: {filepath}")
        return pd.DataFrame()
    
    df = pd.read_csv(filepath)
    
    # Normalize column names
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
    
    return df


def merge_newsletters_with_stats(
    raw_df: Optional[pd.DataFrame] = None,
    stats_df: Optional[pd.DataFrame] = None
) -> pd.DataFrame:
    """
    Merge scraped newsletter data with performance stats.
    
    Performs an inner join on title (case-insensitive, stripped).
    Falls back to URL matching if title doesn't match.
    """
    if raw_df is None:
        raw_df = load_raw_newsletters()
    if stats_df is None:
        stats_df = load_stats_csv()
    
    if raw_df.empty:
        print("Warning: No raw newsletter data to merge")
        return stats_df if not stats_df.empty else pd.DataFrame()
    
    if stats_df.empty:
        print("Warning: No stats data to merge - returning raw data with empty stats")
        raw_df['views'] = None
        raw_df['open_rate'] = None
        return raw_df
    
    # Create normalized title columns for matching
    raw_df['_title_norm'] = raw_df['title'].str.strip().str.lower()
    stats_df['_title_norm'] = stats_df['title'].str.strip().str.lower()
    
    # Merge on normalized title
    merged = pd.merge(
        raw_df,
        stats_df,
        on='_title_norm',
        how='left',
        suffixes=('', '_stats')
    )
    
    # Use stats values where available, fall back to raw values
    if 'date_stats' in merged.columns:
        merged['date'] = merged['date_stats'].fillna(merged.get('published_date', ''))
    elif 'published_date' in merged.columns:
        merged['date'] = merged['published_date']
    
    if 'url_stats' in merged.columns:
        merged['url'] = merged['url'].fillna(merged['url_stats'])
    
    if 'title_stats' in merged.columns:
        merged['title'] = merged['title'].fillna(merged['title_stats'])
    
    # Clean up temporary and duplicate columns
    cols_to_drop = [col for col in merged.columns if col.endswith('_stats') or col.startswith('_')]
    merged = merged.drop(columns=cols_to_drop, errors='ignore')
    
    # Log unmatched entries
    unmatched = merged['views'].isna().sum() if 'views' in merged.columns else 0
    if unmatched > 0:
        print(f"Warning: {unmatched} newsletters have no matching stats data")
    
    return merged


def get_merged_data() -> pd.DataFrame:
    """Convenience function to load and merge all data."""
    return merge_newsletters_with_stats()


# ============================================================================
# Text Processing Utilities
# ============================================================================

def html_to_text(html: str) -> str:
    """Convert HTML content to plain text."""
    if not html:
        return ""
    
    soup = BeautifulSoup(html, 'lxml')
    
    # Remove script and style elements
    for elem in soup(['script', 'style']):
        elem.decompose()
    
    text = soup.get_text(separator=' ', strip=True)
    text = unescape(text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def get_paragraphs(html: str) -> list[str]:
    """Extract paragraphs from HTML content."""
    if not html:
        return []
    
    soup = BeautifulSoup(html, 'lxml')
    
    paragraphs = []
    for p in soup.find_all(['p', 'li']):
        text = p.get_text(strip=True)
        if text and len(text) > 10:  # Skip very short paragraphs
            paragraphs.append(text)
    
    return paragraphs


# ============================================================================
# Headline Heuristics
# ============================================================================

def compute_headline_features(title: str) -> dict:
    """Compute heuristic features for a headline."""
    if not title:
        return {
            'headline_word_count': 0,
            'has_colon': False,
            'has_question_mark': False,
            'starts_with_number': False,
            'contains_strong_verbs': False,
            'contains_ai_term': False,
        }
    
    title_lower = title.lower()
    words = title.split()
    
    # Basic counts
    word_count = len(words)
    
    # Punctuation flags
    has_colon = ':' in title
    has_question_mark = '?' in title
    
    # Starts with number
    starts_with_number = bool(re.match(r'^\d+', title.strip()))
    
    # Strong verbs check
    strong_verbs = CONFIG.get('strong_verbs', [])
    contains_strong_verbs = any(
        verb.lower() in title_lower for verb in strong_verbs
    )
    
    # AI terms check
    ai_terms = CONFIG.get('ai_terms', [])
    contains_ai_term = any(
        term.lower() in title_lower for term in ai_terms
    )
    
    return {
        'headline_word_count': word_count,
        'has_colon': has_colon,
        'has_question_mark': has_question_mark,
        'starts_with_number': starts_with_number,
        'contains_strong_verbs': contains_strong_verbs,
        'contains_ai_term': contains_ai_term,
    }


def classify_headline_length(word_count: int) -> str:
    """Classify headline length into buckets."""
    if word_count <= 5:
        return "very_short (1-5)"
    elif word_count <= 10:
        return "short (6-10)"
    elif word_count <= 15:
        return "medium (11-15)"
    else:
        return "long (16+)"


# ============================================================================
# Topic Classification
# ============================================================================

def classify_topics(title: str, content: str = "") -> dict:
    """Classify a newsletter into topic categories based on keywords."""
    text = f"{title} {content}".lower()
    
    topics_config = CONFIG.get('topics', {})
    topic_flags = {}
    
    for topic_name, keywords in topics_config.items():
        has_topic = any(kw.lower() in text for kw in keywords)
        topic_flags[f'topic_{topic_name}'] = has_topic
    
    return topic_flags


def get_primary_topic(topic_flags: dict) -> str:
    """Get the primary (first matching) topic from topic flags."""
    for key, value in topic_flags.items():
        if value:
            return key.replace('topic_', '')
    return 'general'


# ============================================================================
# Body Structure Analysis
# ============================================================================

def compute_body_features(content_html: str) -> dict:
    """Compute structural features for the body content."""
    if not content_html:
        return {
            'paragraph_count': 0,
            'avg_paragraph_length_words': 0,
            'total_word_count': 0,
            'reading_level': 'unknown',
        }
    
    paragraphs = get_paragraphs(content_html)
    paragraph_count = len(paragraphs)
    
    if paragraph_count == 0:
        return {
            'paragraph_count': 0,
            'avg_paragraph_length_words': 0,
            'total_word_count': 0,
            'reading_level': 'unknown',
        }
    
    # Word counts per paragraph
    word_counts = [len(p.split()) for p in paragraphs]
    total_words = sum(word_counts)
    avg_paragraph_length = total_words / paragraph_count if paragraph_count > 0 else 0
    
    # Very rough reading level estimate based on average word length
    plain_text = html_to_text(content_html)
    words = plain_text.split()
    if words:
        avg_word_length = sum(len(w) for w in words) / len(words)
        if avg_word_length < 4.5:
            reading_level = 'easy'
        elif avg_word_length < 5.5:
            reading_level = 'moderate'
        else:
            reading_level = 'complex'
    else:
        reading_level = 'unknown'
    
    return {
        'paragraph_count': paragraph_count,
        'avg_paragraph_length_words': round(avg_paragraph_length, 1),
        'total_word_count': total_words,
        'reading_level': reading_level,
    }


# ============================================================================
# Feature Computation for Full Dataset
# ============================================================================

def compute_all_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add all heuristic features to a DataFrame of newsletters."""
    df = df.copy()
    
    # Headline features
    headline_features = df['title'].apply(compute_headline_features)
    headline_df = pd.DataFrame(headline_features.tolist())
    
    # Headline length bucket
    headline_df['headline_length_bucket'] = headline_df['headline_word_count'].apply(
        classify_headline_length
    )
    
    # Topic classification
    content_col = 'content_html' if 'content_html' in df.columns else None
    if content_col:
        topic_flags = df.apply(
            lambda row: classify_topics(row['title'], row.get(content_col, '')),
            axis=1
        )
    else:
        topic_flags = df['title'].apply(lambda t: classify_topics(t, ''))
    topic_df = pd.DataFrame(topic_flags.tolist())
    
    # Primary topic
    topic_df['primary_topic'] = topic_df.apply(get_primary_topic, axis=1)
    
    # Body features
    if content_col and content_col in df.columns:
        body_features = df[content_col].apply(compute_body_features)
        body_df = pd.DataFrame(body_features.tolist())
    else:
        body_df = pd.DataFrame({
            'paragraph_count': [0] * len(df),
            'avg_paragraph_length_words': [0] * len(df),
            'total_word_count': [0] * len(df),
            'reading_level': ['unknown'] * len(df),
        })
    
    # Combine all features
    result = pd.concat([df, headline_df, topic_df, body_df], axis=1)
    
    return result


# ============================================================================
# Pattern Analysis Helpers
# ============================================================================

def get_top_n_by_open_rate(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Return top N newsletters by open rate."""
    if 'open_rate' not in df.columns:
        print("Warning: 'open_rate' column not found")
        return df.head(n)
    
    # Filter out rows with missing open_rate
    valid_df = df[df['open_rate'].notna()].copy()
    
    return valid_df.nlargest(n, 'open_rate')


def get_top_n_by_views(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Return top N newsletters by views."""
    if 'views' not in df.columns:
        print("Warning: 'views' column not found")
        return df.head(n)
    
    valid_df = df[df['views'].notna()].copy()
    
    return valid_df.nlargest(n, 'views')


def describe_feature_correlations(df: pd.DataFrame) -> dict:
    """
    Compute and return correlations/group means for key features.
    Returns a dict with analysis results.
    """
    results = {}
    
    if 'open_rate' not in df.columns or df['open_rate'].isna().all():
        print("Warning: No open_rate data available for correlation analysis")
        return results
    
    # Filter to rows with valid open_rate
    valid_df = df[df['open_rate'].notna()].copy()
    
    if len(valid_df) < 3:
        print("Warning: Not enough data for meaningful correlation analysis")
        return results
    
    # Binary feature comparisons
    binary_features = ['has_colon', 'has_question_mark', 'starts_with_number', 
                       'contains_strong_verbs', 'contains_ai_term']
    
    for feature in binary_features:
        if feature in valid_df.columns:
            group_means = valid_df.groupby(feature)['open_rate'].mean()
            results[feature] = {
                'True': group_means.get(True, 0),
                'False': group_means.get(False, 0),
                'difference': group_means.get(True, 0) - group_means.get(False, 0),
            }
    
    # Headline length bucket comparison
    if 'headline_length_bucket' in valid_df.columns:
        bucket_means = valid_df.groupby('headline_length_bucket')['open_rate'].mean()
        results['headline_length_bucket'] = bucket_means.to_dict()
    
    # Topic comparisons
    topic_cols = [col for col in valid_df.columns if col.startswith('topic_')]
    for topic_col in topic_cols:
        if topic_col in valid_df.columns:
            group_means = valid_df.groupby(topic_col)['open_rate'].mean()
            results[topic_col] = {
                'True': group_means.get(True, 0),
                'False': group_means.get(False, 0),
            }
    
    # Primary topic comparison
    if 'primary_topic' in valid_df.columns:
        topic_means = valid_df.groupby('primary_topic')['open_rate'].mean()
        results['primary_topic'] = topic_means.to_dict()
    
    return results


def print_correlation_summary(correlations: dict):
    """Print a formatted summary of correlation analysis."""
    print("\n" + "=" * 60)
    print("PATTERN ANALYSIS: Open Rate Correlations")
    print("=" * 60)
    
    for feature, data in correlations.items():
        print(f"\n{feature}:")
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, float):
                    print(f"  {key}: {value:.2%}")
                else:
                    print(f"  {key}: {value}")


# ============================================================================
# Reach Optimization Score
# ============================================================================

def compute_reach_score(
    title: str,
    body_html: str = "",
    preview: str = ""
) -> tuple[int, list[str]]:
    """
    Compute a 'Reach Optimization Score' (0-100) for a draft.
    
    Returns:
        score: int (0-100)
        feedback: list of feedback strings
    """
    score = 50  # Start at neutral
    feedback = []
    
    # Headline analysis
    headline_features = compute_headline_features(title)
    word_count = headline_features['headline_word_count']
    
    # Optimal headline length: 6-12 words
    if 6 <= word_count <= 12:
        score += 10
        feedback.append("✓ Headline length is optimal (6-12 words)")
    elif word_count < 4:
        score -= 15
        feedback.append("✗ Headline is too short - add more context")
    elif word_count > 15:
        score -= 10
        feedback.append("⚠ Headline is long - consider trimming")
    else:
        feedback.append("○ Headline length is acceptable")
    
    # Question or colon (engagement drivers)
    if headline_features['has_question_mark']:
        score += 8
        feedback.append("✓ Question headline - good for engagement")
    
    if headline_features['has_colon']:
        score += 5
        feedback.append("✓ Colon structure - creates intrigue")
    
    # Number at start
    if headline_features['starts_with_number']:
        score += 7
        feedback.append("✓ Numbered headline - scannable and specific")
    
    # Strong verbs
    if headline_features['contains_strong_verbs']:
        score += 5
        feedback.append("✓ Uses strong verbs - emotional impact")
    
    # AI terms (relevant for this audience)
    if headline_features['contains_ai_term']:
        score += 3
        feedback.append("✓ Contains AI terminology - relevant to audience")
    
    # Preview/subtitle analysis
    if preview:
        preview_words = len(preview.split())
        if 10 <= preview_words <= 30:
            score += 5
            feedback.append("✓ Preview length is good")
        elif preview_words < 5:
            score -= 5
            feedback.append("⚠ Preview is too short - expand it")
        elif preview_words > 50:
            score -= 5
            feedback.append("⚠ Preview is too long - trim for impact")
    else:
        score -= 5
        feedback.append("⚠ No preview provided - add a compelling subtitle")
    
    # Body analysis
    if body_html:
        body_features = compute_body_features(body_html)
        
        # Paragraph structure
        para_count = body_features['paragraph_count']
        avg_para_len = body_features['avg_paragraph_length_words']
        
        if para_count >= 5:
            score += 5
            feedback.append("✓ Good paragraph structure")
        elif para_count < 3 and body_features['total_word_count'] > 100:
            score -= 5
            feedback.append("⚠ Consider breaking content into more paragraphs")
        
        if 20 <= avg_para_len <= 60:
            score += 5
            feedback.append("✓ Paragraph length is readable")
        elif avg_para_len > 100:
            score -= 10
            feedback.append("⚠ Paragraphs are too long - break them up")
    
    # Clamp score to 0-100
    score = max(0, min(100, score))
    
    return score, feedback


# ============================================================================
# Main (for testing)
# ============================================================================

if __name__ == "__main__":
    print("Loading and merging newsletter data...")
    
    df = get_merged_data()
    
    if df.empty:
        print("No data available. Run the scraper first:")
        print("  python scrape_substack.py")
    else:
        print(f"Loaded {len(df)} newsletters")
        
        # Compute features
        df = compute_all_features(df)
        
        # Show top performers
        print("\nTop 5 by open rate:")
        top_5 = get_top_n_by_open_rate(df, 5)
        if not top_5.empty:
            for _, row in top_5.iterrows():
                print(f"  {row.get('open_rate', 'N/A'):.0%} - {row['title'][:60]}...")
        
        # Show correlations
        correlations = describe_feature_correlations(df)
        print_correlation_summary(correlations)









